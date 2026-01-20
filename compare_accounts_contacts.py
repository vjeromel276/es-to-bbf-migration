#!/usr/bin/env python3
"""
Compare Accounts and Contacts between BBF and ES Salesforce Orgs
OPTIMIZED VERSION - Uses blocking and rapidfuzz for speed

Generates an Excel workbook with:
  - Tab 1: BBF Accounts
  - Tab 2: ES Accounts
  - Tab 3: Account Matches by Name
  - Tab 4: Account Matches (Name + Address)
  - Tab 5: BBF Contacts
  - Tab 6: ES Contacts
  - Tab 7: Contact Matches by Name
  - Tab 8: Contact Matches (Name + Email)
"""

import sys
import pandas as pd
from simple_salesforce import Salesforce
from rapidfuzz import fuzz
from collections import defaultdict
import re

# Import credentials from .env file
from credentials import get_es_credentials, get_bbf_credentials

# ---------------------------------------------------------------------
# Salesforce credentials - loaded from .env file
# ---------------------------------------------------------------------
BBF_CREDENTIALS = get_bbf_credentials()
ES_CREDENTIALS = get_es_credentials('prod')

# ---------------------------------------------------------------------
# Standard Account fields to retrieve
# ---------------------------------------------------------------------
ACCOUNT_FIELDS = [
    "Id",
    "Name",
    "BillingStreet",
    "BillingCity",
    "BillingState",
    "BillingPostalCode",
    "BillingCountry",
    "ShippingStreet",
    "ShippingCity",
    "ShippingState",
    "ShippingPostalCode",
    "ShippingCountry",
    "Phone",
    "Fax",
    "Website",
    "Type",
    "Industry",
    "Description",
]

# ---------------------------------------------------------------------
# Standard Contact fields to retrieve
# ---------------------------------------------------------------------
CONTACT_FIELDS = [
    "Id",
    "FirstName",
    "LastName",
    "Name",
    "AccountId",
    "Email",
    "Phone",
    "MobilePhone",
    "Title",
    "Department",
    "MailingStreet",
    "MailingCity",
    "MailingState",
    "MailingPostalCode",
    "MailingCountry",
]


def connect_to_salesforce(credentials, org_name):
    """Connect to a Salesforce org and return the connection object."""
    print(f"\n🔌 Connecting to {org_name} Salesforce...")
    try:
        sf = Salesforce(
            username=credentials["username"],
            password=credentials["password"],
            security_token=credentials["security_token"],
            domain=credentials["domain"],
        )
        print(f"✅ Connected to {org_name}: {sf.sf_instance}")
        return sf
    except Exception as e:
        print(f"❌ Error connecting to {org_name}: {e}")
        return None


def get_available_fields(sf, object_name):
    """Get list of available fields for an object."""
    try:
        desc = sf.__getattr__(object_name).describe()
        return [f["name"] for f in desc.get("fields", [])]
    except Exception as e:
        print(f"⚠️ Error getting fields: {e}")
        return []


def fetch_records(sf, org_name, object_name, field_list):
    """
    Fetch all records for a given object from a Salesforce org.
    Uses only standard fields.
    """
    print(f"\n📡 Fetching {object_name} records from {org_name}...")

    # Get available fields to check which ones exist
    available_fields = get_available_fields(sf, object_name)

    # Filter to only fields that exist in this org
    fields_to_query = [f for f in field_list if f in available_fields]

    # Build query - no WHERE clause, just get all records
    fields_str = ", ".join(fields_to_query)
    query = f"SELECT {fields_str} FROM {object_name}"

    print(f"📋 Querying {len(fields_to_query)} fields...")

    try:
        # Use query_all to handle large result sets
        results = sf.query_all(query)
        records = results.get("records", [])

        # Clean up records (remove Salesforce metadata)
        cleaned_records = []
        for record in records:
            clean_record = {k: v for k, v in record.items() if k != "attributes"}
            cleaned_records.append(clean_record)

        print(
            f"✅ Retrieved {len(cleaned_records)} {object_name} records from {org_name}"
        )
        return cleaned_records

    except Exception as e:
        print(f"❌ Error querying {org_name}: {e}")
        return []


def normalize_string(s):
    """Normalize a string for comparison (lowercase, remove extra spaces, etc.)"""
    if s is None:
        return ""
    # Convert to string, lowercase, remove extra whitespace
    s = str(s).lower().strip()
    # Remove common suffixes that might differ
    s = re.sub(
        r"\s+(inc\.?|llc\.?|ltd\.?|corp\.?|co\.?|company)$", "", s, flags=re.IGNORECASE
    )
    # Remove punctuation
    s = re.sub(r"[^\w\s]", "", s)
    # Normalize whitespace
    s = re.sub(r"\s+", " ", s)
    return s


def get_blocking_keys(name):
    """
    Generate blocking keys for a name.
    This reduces the search space by only comparing records with similar keys.
    """
    norm = normalize_string(name)
    if not norm:
        return set()

    keys = set()

    # Key 1: First 3 characters (or full name if shorter)
    keys.add(norm[:3])

    # Key 2: First word
    first_word = norm.split()[0] if norm.split() else ""
    if first_word:
        keys.add(first_word[:4])  # First 4 chars of first word

    # Key 3: Sorted first letters of each word (catches reordering)
    words = norm.split()
    if len(words) > 1:
        sorted_initials = "".join(sorted([w[0] for w in words if w]))
        keys.add(sorted_initials)

    return keys


def normalize_address(street, city, state, postal):
    """Create a normalized address string for comparison."""
    parts = []
    for part in [street, city, state, postal]:
        if part:
            parts.append(normalize_string(str(part)))
    return " ".join(parts)


def normalize_email(email):
    """Normalize email for comparison."""
    if email is None:
        return ""
    return str(email).lower().strip()


def find_account_name_matches_optimized(bbf_df, es_df, threshold=85):
    """
    Find accounts that match by name between BBF and ES.
    Uses blocking to reduce comparisons and rapidfuzz for speed.
    Threshold is 0-100 (rapidfuzz scale).
    """
    print(f"\n🔍 Finding account name matches (threshold: {threshold}%)...")
    print(f"   Building blocking index for {len(es_df)} ES accounts...")

    # Build blocking index for ES accounts
    es_blocks = defaultdict(list)
    for idx, row in es_df.iterrows():
        es_name = row.get("Name", "")
        keys = get_blocking_keys(es_name)
        for key in keys:
            es_blocks[key].append((idx, row))

    print(f"   Created {len(es_blocks)} blocking buckets")
    print(f"   Matching {len(bbf_df)} BBF accounts...")

    matches = []
    seen_pairs = set()  # Avoid duplicate matches

    processed = 0
    for _, bbf_row in bbf_df.iterrows():
        bbf_name = bbf_row.get("Name", "")
        bbf_name_norm = normalize_string(bbf_name)

        if not bbf_name_norm:
            continue

        # Get blocking keys for this BBF account
        bbf_keys = get_blocking_keys(bbf_name)

        # Find candidate ES accounts from matching blocks
        candidates = set()
        for key in bbf_keys:
            if key in es_blocks:
                for es_idx, es_row in es_blocks[key]:
                    candidates.add((es_idx, es_row.get("Id", "")))

        # Compare with candidates only
        for es_idx, es_id in candidates:
            pair_key = (bbf_row.get("Id", ""), es_id)
            if pair_key in seen_pairs:
                continue

            es_row = es_df.iloc[es_idx]
            es_name = es_row.get("Name", "")
            es_name_norm = normalize_string(es_name)

            if not es_name_norm:
                continue

            # Use rapidfuzz for fast comparison
            similarity = fuzz.ratio(bbf_name_norm, es_name_norm)

            if similarity >= threshold:
                seen_pairs.add(pair_key)
                match_record = {
                    "BBF_Id": bbf_row.get("Id", ""),
                    "BBF_Name": bbf_name,
                    "ES_Id": es_id,
                    "ES_Name": es_name,
                    "Name_Similarity": round(
                        similarity / 100, 3
                    ),  # Convert to 0-1 scale
                    "BBF_BillingCity": bbf_row.get("BillingCity", ""),
                    "ES_BillingCity": es_row.get("BillingCity", ""),
                    "BBF_BillingState": bbf_row.get("BillingState", ""),
                    "ES_BillingState": es_row.get("BillingState", ""),
                    "BBF_Phone": bbf_row.get("Phone", ""),
                    "ES_Phone": es_row.get("Phone", ""),
                }
                matches.append(match_record)

        processed += 1
        if processed % 1000 == 0:
            print(
                f"   Processed {processed}/{len(bbf_df)} BBF accounts, found {len(matches)} matches so far..."
            )

    print(f"✅ Found {len(matches)} potential account name matches")
    return matches


def find_account_address_matches(name_matches_df, bbf_df, es_df, threshold=60):
    """
    Refine account name matches by also checking address similarity.
    Threshold is 0-100 scale.
    """
    print(f"\n🔍 Refining account matches by address (threshold: {threshold}%)...")

    # Create lookup dictionaries for faster access
    bbf_lookup = bbf_df.set_index("Id").to_dict("index")
    es_lookup = es_df.set_index("Id").to_dict("index")

    refined_matches = []

    for _, match in name_matches_df.iterrows():
        bbf_id = match.get("BBF_Id", "")
        es_id = match.get("ES_Id", "")

        bbf_record = bbf_lookup.get(bbf_id, {})
        es_record = es_lookup.get(es_id, {})

        # Normalize billing addresses
        bbf_billing = normalize_address(
            bbf_record.get("BillingStreet"),
            bbf_record.get("BillingCity"),
            bbf_record.get("BillingState"),
            bbf_record.get("BillingPostalCode"),
        )

        es_billing = normalize_address(
            es_record.get("BillingStreet"),
            es_record.get("BillingCity"),
            es_record.get("BillingState"),
            es_record.get("BillingPostalCode"),
        )

        # Calculate address similarity using rapidfuzz
        if bbf_billing and es_billing:
            address_similarity = fuzz.ratio(bbf_billing, es_billing)
        else:
            address_similarity = 0

        # Also check shipping address
        bbf_shipping = normalize_address(
            bbf_record.get("ShippingStreet"),
            bbf_record.get("ShippingCity"),
            bbf_record.get("ShippingState"),
            bbf_record.get("ShippingPostalCode"),
        )

        es_shipping = normalize_address(
            es_record.get("ShippingStreet"),
            es_record.get("ShippingCity"),
            es_record.get("ShippingState"),
            es_record.get("ShippingPostalCode"),
        )

        if bbf_shipping and es_shipping:
            shipping_similarity = fuzz.ratio(bbf_shipping, es_shipping)
        else:
            shipping_similarity = 0

        # Use the better of billing or shipping match
        best_address_similarity = max(address_similarity, shipping_similarity)

        if best_address_similarity >= threshold:
            refined_record = {
                "BBF_Id": bbf_id,
                "BBF_Name": match.get("BBF_Name", ""),
                "ES_Id": es_id,
                "ES_Name": match.get("ES_Name", ""),
                "Name_Similarity": match.get("Name_Similarity", 0),
                "Address_Similarity": round(best_address_similarity / 100, 3),
                "BBF_BillingStreet": bbf_record.get("BillingStreet", ""),
                "BBF_BillingCity": bbf_record.get("BillingCity", ""),
                "BBF_BillingState": bbf_record.get("BillingState", ""),
                "BBF_BillingPostalCode": bbf_record.get("BillingPostalCode", ""),
                "ES_BillingStreet": es_record.get("BillingStreet", ""),
                "ES_BillingCity": es_record.get("BillingCity", ""),
                "ES_BillingState": es_record.get("BillingState", ""),
                "ES_BillingPostalCode": es_record.get("BillingPostalCode", ""),
                "Match_Type": (
                    "Billing"
                    if address_similarity >= shipping_similarity
                    else "Shipping"
                ),
            }
            refined_matches.append(refined_record)

    print(f"✅ Found {len(refined_matches)} account matches with address confirmation")
    return refined_matches


def find_contact_name_matches_optimized(bbf_df, es_df, threshold=85):
    """
    Find contacts that match by name between BBF and ES.
    Uses blocking and rapidfuzz for speed.
    """
    print(f"\n🔍 Finding contact name matches (threshold: {threshold}%)...")
    print(f"   Building blocking index for {len(es_df)} ES contacts...")

    # Build blocking index for ES contacts
    es_blocks = defaultdict(list)
    for idx, row in es_df.iterrows():
        es_name = row.get("Name", "")
        keys = get_blocking_keys(es_name)
        for key in keys:
            es_blocks[key].append((idx, row))

    print(f"   Created {len(es_blocks)} blocking buckets")
    print(f"   Matching {len(bbf_df)} BBF contacts...")

    matches = []
    seen_pairs = set()

    processed = 0
    for _, bbf_row in bbf_df.iterrows():
        bbf_name = bbf_row.get("Name", "")
        bbf_name_norm = normalize_string(bbf_name)

        if not bbf_name_norm:
            continue

        bbf_keys = get_blocking_keys(bbf_name)

        candidates = set()
        for key in bbf_keys:
            if key in es_blocks:
                for es_idx, es_row in es_blocks[key]:
                    candidates.add((es_idx, es_row.get("Id", "")))

        for es_idx, es_id in candidates:
            pair_key = (bbf_row.get("Id", ""), es_id)
            if pair_key in seen_pairs:
                continue

            es_row = es_df.iloc[es_idx]
            es_name = es_row.get("Name", "")
            es_name_norm = normalize_string(es_name)

            if not es_name_norm:
                continue

            similarity = fuzz.ratio(bbf_name_norm, es_name_norm)

            if similarity >= threshold:
                seen_pairs.add(pair_key)
                match_record = {
                    "BBF_Id": bbf_row.get("Id", ""),
                    "BBF_Name": bbf_name,
                    "BBF_FirstName": bbf_row.get("FirstName", ""),
                    "BBF_LastName": bbf_row.get("LastName", ""),
                    "ES_Id": es_id,
                    "ES_Name": es_name,
                    "ES_FirstName": es_row.get("FirstName", ""),
                    "ES_LastName": es_row.get("LastName", ""),
                    "Name_Similarity": round(similarity / 100, 3),
                    "BBF_Email": bbf_row.get("Email", ""),
                    "ES_Email": es_row.get("Email", ""),
                    "BBF_Phone": bbf_row.get("Phone", ""),
                    "ES_Phone": es_row.get("Phone", ""),
                    "BBF_Title": bbf_row.get("Title", ""),
                    "ES_Title": es_row.get("Title", ""),
                }
                matches.append(match_record)

        processed += 1
        if processed % 1000 == 0:
            print(
                f"   Processed {processed}/{len(bbf_df)} BBF contacts, found {len(matches)} matches so far..."
            )

    print(f"✅ Found {len(matches)} potential contact name matches")
    return matches


def find_contact_email_matches(name_matches_df, bbf_df, es_df):
    """
    Refine contact name matches by also checking email match.
    """
    print(f"\n🔍 Refining contact matches by email...")

    # Create lookup dictionaries for faster access
    bbf_lookup = bbf_df.set_index("Id").to_dict("index")
    es_lookup = es_df.set_index("Id").to_dict("index")

    refined_matches = []

    for _, match in name_matches_df.iterrows():
        bbf_id = match.get("BBF_Id", "")
        es_id = match.get("ES_Id", "")

        bbf_record = bbf_lookup.get(bbf_id, {})
        es_record = es_lookup.get(es_id, {})

        bbf_email = normalize_email(bbf_record.get("Email"))
        es_email = normalize_email(es_record.get("Email"))

        # Check for email match (exact or high similarity)
        if bbf_email and es_email:
            email_similarity = fuzz.ratio(bbf_email, es_email)
            email_match = email_similarity >= 90
        else:
            email_match = False
            email_similarity = 0

        if email_match:
            refined_record = {
                "BBF_Id": bbf_id,
                "BBF_Name": match.get("BBF_Name", ""),
                "BBF_FirstName": match.get("BBF_FirstName", ""),
                "BBF_LastName": match.get("BBF_LastName", ""),
                "ES_Id": es_id,
                "ES_Name": match.get("ES_Name", ""),
                "ES_FirstName": match.get("ES_FirstName", ""),
                "ES_LastName": match.get("ES_LastName", ""),
                "Name_Similarity": match.get("Name_Similarity", 0),
                "Email_Similarity": round(email_similarity / 100, 3),
                "BBF_Email": bbf_record.get("Email", ""),
                "ES_Email": es_record.get("Email", ""),
                "BBF_Phone": bbf_record.get("Phone", ""),
                "ES_Phone": es_record.get("Phone", ""),
                "BBF_Title": bbf_record.get("Title", ""),
                "ES_Title": es_record.get("Title", ""),
                "BBF_AccountId": bbf_record.get("AccountId", ""),
                "ES_AccountId": es_record.get("AccountId", ""),
            }
            refined_matches.append(refined_record)

    print(f"✅ Found {len(refined_matches)} contact matches with email confirmation")
    return refined_matches


def main():
    print("=" * 60)
    print("BBF / ES Account & Contact Comparison Tool (OPTIMIZED)")
    print("=" * 60)

    # Connect to both orgs
    bbf_sf = connect_to_salesforce(BBF_CREDENTIALS, "BBF")
    es_sf = connect_to_salesforce(ES_CREDENTIALS, "ES")

    if not bbf_sf or not es_sf:
        print("\n❌ Failed to connect to one or both orgs. Exiting.")
        sys.exit(1)

    # =====================================================================
    # ACCOUNTS
    # =====================================================================
    print("\n" + "=" * 60)
    print("PROCESSING ACCOUNTS")
    print("=" * 60)

    bbf_accounts = fetch_records(bbf_sf, "BBF", "Account", ACCOUNT_FIELDS)
    es_accounts = fetch_records(es_sf, "ES", "Account", ACCOUNT_FIELDS)

    bbf_acct_df = pd.DataFrame(bbf_accounts) if bbf_accounts else pd.DataFrame()
    es_acct_df = pd.DataFrame(es_accounts) if es_accounts else pd.DataFrame()

    print(f"\n📊 Account Summary:")
    print(f"   BBF Accounts: {len(bbf_acct_df)}")
    print(f"   ES Accounts:  {len(es_acct_df)}")

    # Find account matches (optimized)
    if not bbf_acct_df.empty and not es_acct_df.empty:
        acct_name_matches = find_account_name_matches_optimized(
            bbf_acct_df, es_acct_df, threshold=85
        )
        acct_name_matches_df = (
            pd.DataFrame(acct_name_matches) if acct_name_matches else pd.DataFrame()
        )

        if not acct_name_matches_df.empty:
            acct_addr_matches = find_account_address_matches(
                acct_name_matches_df, bbf_acct_df, es_acct_df, threshold=60
            )
            acct_addr_matches_df = (
                pd.DataFrame(acct_addr_matches) if acct_addr_matches else pd.DataFrame()
            )
        else:
            acct_addr_matches_df = pd.DataFrame()
    else:
        acct_name_matches_df = pd.DataFrame()
        acct_addr_matches_df = pd.DataFrame()

    # =====================================================================
    # CONTACTS
    # =====================================================================
    print("\n" + "=" * 60)
    print("PROCESSING CONTACTS")
    print("=" * 60)

    bbf_contacts = fetch_records(bbf_sf, "BBF", "Contact", CONTACT_FIELDS)
    es_contacts = fetch_records(es_sf, "ES", "Contact", CONTACT_FIELDS)

    bbf_cont_df = pd.DataFrame(bbf_contacts) if bbf_contacts else pd.DataFrame()
    es_cont_df = pd.DataFrame(es_contacts) if es_contacts else pd.DataFrame()

    print(f"\n📊 Contact Summary:")
    print(f"   BBF Contacts: {len(bbf_cont_df)}")
    print(f"   ES Contacts:  {len(es_cont_df)}")

    # Find contact matches (optimized)
    if not bbf_cont_df.empty and not es_cont_df.empty:
        cont_name_matches = find_contact_name_matches_optimized(
            bbf_cont_df, es_cont_df, threshold=85
        )
        cont_name_matches_df = (
            pd.DataFrame(cont_name_matches) if cont_name_matches else pd.DataFrame()
        )

        if not cont_name_matches_df.empty:
            cont_email_matches = find_contact_email_matches(
                cont_name_matches_df, bbf_cont_df, es_cont_df
            )
            cont_email_matches_df = (
                pd.DataFrame(cont_email_matches)
                if cont_email_matches
                else pd.DataFrame()
            )
        else:
            cont_email_matches_df = pd.DataFrame()
    else:
        cont_name_matches_df = pd.DataFrame()
        cont_email_matches_df = pd.DataFrame()

    # =====================================================================
    # EXPORT TO EXCEL
    # =====================================================================
    output_file = "account_contact_comparison.xlsx"
    print(f"\n📝 Writing results to {output_file}...")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Tab 1: BBF Accounts
        if not bbf_acct_df.empty:
            bbf_acct_df.to_excel(writer, index=False, sheet_name="BBF_Accounts")
            print(f"   ✅ BBF_Accounts: {len(bbf_acct_df)} rows")
        else:
            pd.DataFrame({"Message": ["No accounts found"]}).to_excel(
                writer, index=False, sheet_name="BBF_Accounts"
            )

        # Tab 2: ES Accounts
        if not es_acct_df.empty:
            es_acct_df.to_excel(writer, index=False, sheet_name="ES_Accounts")
            print(f"   ✅ ES_Accounts: {len(es_acct_df)} rows")
        else:
            pd.DataFrame({"Message": ["No accounts found"]}).to_excel(
                writer, index=False, sheet_name="ES_Accounts"
            )

        # Tab 3: Account Name Matches
        if not acct_name_matches_df.empty:
            acct_name_matches_df = acct_name_matches_df.sort_values(
                "Name_Similarity", ascending=False
            )
            acct_name_matches_df.to_excel(
                writer, index=False, sheet_name="Acct_Name_Matches"
            )
            print(f"   ✅ Acct_Name_Matches: {len(acct_name_matches_df)} rows")
        else:
            pd.DataFrame({"Message": ["No name matches found"]}).to_excel(
                writer, index=False, sheet_name="Acct_Name_Matches"
            )

        # Tab 4: Account Address Confirmed
        if not acct_addr_matches_df.empty:
            acct_addr_matches_df["Combined_Score"] = (
                acct_addr_matches_df["Name_Similarity"]
                + acct_addr_matches_df["Address_Similarity"]
            ) / 2
            acct_addr_matches_df = acct_addr_matches_df.sort_values(
                "Combined_Score", ascending=False
            )
            acct_addr_matches_df.to_excel(
                writer, index=False, sheet_name="Acct_Addr_Confirmed"
            )
            print(f"   ✅ Acct_Addr_Confirmed: {len(acct_addr_matches_df)} rows")
        else:
            pd.DataFrame({"Message": ["No address-confirmed matches found"]}).to_excel(
                writer, index=False, sheet_name="Acct_Addr_Confirmed"
            )

        # Tab 5: BBF Contacts
        if not bbf_cont_df.empty:
            bbf_cont_df.to_excel(writer, index=False, sheet_name="BBF_Contacts")
            print(f"   ✅ BBF_Contacts: {len(bbf_cont_df)} rows")
        else:
            pd.DataFrame({"Message": ["No contacts found"]}).to_excel(
                writer, index=False, sheet_name="BBF_Contacts"
            )

        # Tab 6: ES Contacts
        if not es_cont_df.empty:
            es_cont_df.to_excel(writer, index=False, sheet_name="ES_Contacts")
            print(f"   ✅ ES_Contacts: {len(es_cont_df)} rows")
        else:
            pd.DataFrame({"Message": ["No contacts found"]}).to_excel(
                writer, index=False, sheet_name="ES_Contacts"
            )

        # Tab 7: Contact Name Matches
        if not cont_name_matches_df.empty:
            cont_name_matches_df = cont_name_matches_df.sort_values(
                "Name_Similarity", ascending=False
            )
            cont_name_matches_df.to_excel(
                writer, index=False, sheet_name="Cont_Name_Matches"
            )
            print(f"   ✅ Cont_Name_Matches: {len(cont_name_matches_df)} rows")
        else:
            pd.DataFrame({"Message": ["No name matches found"]}).to_excel(
                writer, index=False, sheet_name="Cont_Name_Matches"
            )

        # Tab 8: Contact Email Confirmed
        if not cont_email_matches_df.empty:
            cont_email_matches_df["Combined_Score"] = (
                cont_email_matches_df["Name_Similarity"]
                + cont_email_matches_df["Email_Similarity"]
            ) / 2
            cont_email_matches_df = cont_email_matches_df.sort_values(
                "Combined_Score", ascending=False
            )
            cont_email_matches_df.to_excel(
                writer, index=False, sheet_name="Cont_Email_Confirmed"
            )
            print(f"   ✅ Cont_Email_Confirmed: {len(cont_email_matches_df)} rows")
        else:
            pd.DataFrame({"Message": ["No email-confirmed matches found"]}).to_excel(
                writer, index=False, sheet_name="Cont_Email_Confirmed"
            )

    print(f"\n✨ Export complete → {output_file}")

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"  ACCOUNTS:")
    print(f"    BBF Accounts:              {len(bbf_acct_df)}")
    print(f"    ES Accounts:               {len(es_acct_df)}")
    print(f"    Name Matches:              {len(acct_name_matches_df)}")
    print(f"    Address-Confirmed:         {len(acct_addr_matches_df)}")
    print(f"  CONTACTS:")
    print(f"    BBF Contacts:              {len(bbf_cont_df)}")
    print(f"    ES Contacts:               {len(es_cont_df)}")
    print(f"    Name Matches:              {len(cont_name_matches_df)}")
    print(f"    Email-Confirmed:           {len(cont_email_matches_df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
