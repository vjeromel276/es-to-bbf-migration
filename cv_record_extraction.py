"""
BBF Order Extract Script
========================
Extracts all Orders matching the BBF filter criteria, plus all related
Address__c and Facility__c records. Outputs three CSV files.

Requirements:
    pip install simple-salesforce pandas

Usage:
    1. Set your Salesforce credentials in the CONFIGURATION section below.
    2. Run: python bbf_order_extract.py
    3. Three CSV files will be created in the output directory.

Connection Options:
    - Username/Password + Security Token (default)
    - Or set SESSION_ID and INSTANCE_URL for an existing session
"""

import csv
import os
import sys
from datetime import datetime
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

# =============================================================================
# CONFIGURATION — Update these values before running
# =============================================================================

# Option 1: Username + Password + Security Token
SF_USERNAME = "sfdcapi@everstream.net"  # e.g. "vincent@everstream.net"
SF_PASSWORD = "pV4CAxns8DQtJsBq!"  # Your Salesforce password
SF_SECURITY_TOKEN = (
    "r1uoYiusK19RbrflARydi86TA"  # Your security token (from Salesforce Settings)
)
SF_DOMAIN = "login"  # "login" for production, "test" for sandbox

# Option 2: Existing session (uncomment and set these, leave Option 1 blank)
# SESSION_ID = ""
# INSTANCE_URL = ""       # e.g. "https://everstream.my.salesforce.com"

# Output directory for CSV files
OUTPUT_DIR = "./bbf_extract_output"

# =============================================================================
# FIELD DEFINITIONS — All fields from each object
# =============================================================================

# Compound/non-queryable field types (address, location) that must be excluded
# from SOQL SELECT. Their component fields are already listed individually.
EXCLUDED_ORDER_FIELDS = {
    "BillingAddress",  # compound address
    "ShippingAddress",  # compound address
    "Power_Location_Lat_Long__c",  # compound location
}

EXCLUDED_ADDRESS_FIELDS = {
    "Geocode_Lat_Long__c",  # compound location
}

EXCLUDED_FACILITY_FIELDS = {
    "Facility_Geolocation__c",  # compound location
}

# --- Order fields (all from es_Order_fields.csv minus compound types) ---
ORDER_FIELDS = [
    "Id",
    "OwnerId",
    "ContractId",
    "AccountId",
    "Pricebook2Id",
    "OriginalOrderId",
    "OpportunityId",
    "QuoteId",
    "RecordTypeId",
    "EffectiveDate",
    "EndDate",
    "IsReductionOrder",
    "Status",
    "Description",
    "CustomerAuthorizedById",
    "CustomerAuthorizedDate",
    "CompanyAuthorizedById",
    "CompanyAuthorizedDate",
    "Type",
    "BillingStreet",
    "BillingCity",
    "BillingState",
    "BillingPostalCode",
    "BillingCountry",
    "BillingLatitude",
    "BillingLongitude",
    "BillingGeocodeAccuracy",
    # BillingAddress excluded (compound)
    "ShippingStreet",
    "ShippingCity",
    "ShippingState",
    "ShippingPostalCode",
    "ShippingCountry",
    "ShippingLatitude",
    "ShippingLongitude",
    "ShippingGeocodeAccuracy",
    # ShippingAddress excluded (compound)
    "Name",
    "PoDate",
    "PoNumber",
    "OrderReferenceNumber",
    "BillToContactId",
    "ShipToContactId",
    "ActivatedDate",
    "ActivatedById",
    "StatusCode",
    "OrderNumber",
    "TotalAmount",
    "CreatedDate",
    "CreatedById",
    "LastModifiedDate",
    "LastModifiedById",
    "IsDeleted",
    "SystemModstamp",
    "LastViewedDate",
    "LastReferencedDate",
    # Custom fields
    "Date_Contact_Made_with_Customer__c",
    "End_Reason_Notes__c",
    "Facility_address_z_a__c",
    "Service_Order_Product_Count__c",
    "Address_A_Building_Status__c",
    "Order_Type_Data_Load__c",
    "NNI__c",
    "Priority_Designation_Notes__c",
    "Order_Link__c",
    "Build_Type_Address_Z__c",
    "Install_Not_Completed__c",
    "Account_Name_Searchable__c",
    "Neustar_CCNA__c",
    "Last_Mile_Carrier__c",
    "SOF_Net_Margin_Addition_Old_to_New_SOF__c",
    "Order_Ack_Sent__c",
    "HIDDEN_PRODUCT_COUNT_LAST_MILE_ONNET__c",
    "Survey_Sent__c",
    "ON_NET_FLAG__c",
    "Off_Net_Record_Generated__c",
    "Survey_Link__c",
    "Service_ID__c",
    "OSS_Order__c",
    "Address_Z_Building_Status__c",
    "Corrective_Order__c",
    "Service_ID_Searchable__c",
    "Total_Vendor_MRC_Offnet__c",
    "Single_Thread_Approval_Received__c",
    "Billable_Work_Order__c",
    "Service_Start_Date__c",
    "Launch_Category__c",
    "Billing_Start_Date__c",
    "Neustar_ERROR_MSG__c",
    "HIDDEN_ACCOUNTING_NOTIFIED_NEW__c",
    "Design_Status__c",
    "Auto_Created_By_MSA_Renewal__c",
    "Neustar_Fatal_Error__c",
    "CCD_Change_Approved__c",
    "Neustar_ERROR_TAG__c",
    "Neustar_VER__c",
    "VLAN_A__c",
    "VLAN_B__c",
    "Delivery_SLA__c",
    "Number_of_Days_From_NTP__c",
    "Billing_Frequency__c",
    "Metro_Act_Footage_Not_Needed__c",
    "CCD_Change_Requested_To__c",
    "Neustar_RCODE__c",
    "Neustar_Supp_Type__c",
    "Cancelled_Has_Been_Set__c",
    "Neustar_CNR_VER__c",
    "Neustar_CNT__c",
    "Ring__c",
    "Node__c",
    "Customer_Category__c",
    "Confirmed_Has_Been_Sent__c",
    "Complete_Has_Been_Sent__c",
    "EST_Construction_Materials_Total__c",
    "CapEx_at_Activation__c",
    "Full_Diversity_FOC__c",
    "CCD_Requestor_Manager_Email__c",
    "IRU_Scheduled_Splice_Date__c",
    "COP_Request_to_Vendor__c",
    "COP_Received_from_Vendor__c",
    "COP_Sent_to_RF__c",
    "EST_Minimum_Lead_Time__c",
    "Power_Ready__c",
    "Small_Cell_Completion_Package_Sent__c",
    "NTP_Requested__c",
    "Neustar_Send_On_Demand_Outbound_Message__c",
    "OSS_Order_Link__c",
    "NNI_CID__c",
    "Additional_Order_Ids_To_Include_In_Email__c",
    "Replacing_Order_Service_ID_Mismatch__c",
    "HIDDEN_CONNECTING_FIBER_SEGMENT__c",
    "Service_Agreement_Full_Term_Revnue__c",
    "Force_Resource_Reset_Based_on_Project__c",
    "Facility_Address_Z_b__c",
    "PO_Grand_Total__c",
    "PO_Count__c",
    "address_AZ_search__c",
    "Design_Proposed_Facility_A__c",
    "Design_Proposed_Facility_Z__c",
    "Completion_Package_Sent__c",
    "Permitting_Contractor__c",
    "Notes_from_Sales_Engineering__c",
    "Notes_from_Sales_Person__c",
    "Service_Order_Agreement_MRC_Amortized__c",
    "Service_Order_Agreement_NRC_Non_Amortiz__c",
    "HIDDED_PROTECTED_CIRCUIT_FLAG__c",
    "ECD_Weeks_Out__c",
    "CCD_Weeks_Out__c",
    "Accounting_Turn_Up_Date__c",
    "Service_Order_Agreement_Replacing__c",
    "SOF_Margin_Replacing_MRC_Vendor_Costs__c",
    "Service_Order_Details_Replacing__c",
    "Order_Type_From_Opportunity__c",
    "Initial_Activation_Date__c",
    "First_Estimated_Completion_Date_ECD__c",
    "Project_Code_Accounting__c",
    "Service_End_Date__c",
    "Disconnected_with_Portability_Clause__c",
    "ServiceEndSub_Reasons__c",
    "Service_End_Reason__c",
    "Service_End_Expected_EFT__c",
    "TSP_Code__c",
    "Equipment_Pickup_Complete__c",
    "Equipment_Pickup_Needed__c",
    "Move_Order_To_SOF_Id__c",
    "Other_Order_Ids_To_Include_In_Email__c",
    "Work_Order_Sync_Verified__c",
    "Product_Sold_Details__c",
    "autoMsaRenewed__c",
    "AssignedTo_User__c",
    "ORDER_FLAGS__c",
    "Billing_Start_Date_Provided__c",
    "Construction_Cost__c",
    "Do_Not_Set_Resource_Needs__c",
    "HIDDEN_ONE_TIME_USE_THEN_DELETE__c",
    "Service_Order_Agreement_Top_Line_Rev__c",
    "SOF_Margin_Replacing_MRC__c",
    "First_Assign_To_Engineer_Status_Date__c",
    "Vendor_Circuit_ID__c",
    "Vendor_Contract_Start_Date__c",
    "Vendor_Activation_Date__c",
    "Vendor_Contract_Term__c",
    "Vendor_Contract_Expiration_Date__c",
    "SOF_Replacing_MRC_Searchable__c",
    "Vendor_Status__c",
    "Vendor_Disconnect_Date__c",
    "Service_Provided__c",
    "Expedite__c",
    "Order_Term_Override__c",
    "Entity__c",
    "Sent_New_Type_2_Notification__c",
    "Vendor_Contract_Account_No__c",
    "Hidden_Status_Disco_In_Progress__c",
    "Cancellation_Date__c",
    "Vendor_Related_Notes__c",
    "auto_closed_opp__c",
    "Fiber_Design_Complete_FDE__c",
    "Date_Synced_To_Billing__c",
    "Vendor_NRC__c",
    # Lines 201-381
    "Field_Maps_Created_OSP__c",
    "Equipment_Installation_Date__c",
    "Business_Sector__c",
    "Hidden_URL_Opportunity__c",
    "Bill_To_Contact_Full_Name__c",
    "Customer_Requested_Due_Date__c",
    "Order_Contact_Stored__c",
    "OSP_Design_Comments__c",
    "Related_Opportunity_Name__c",
    "Sales_Comments_for_Sales_Engineer__c",
    "Field_Maps_Revised_OSP__c",
    "Quoted_ETF__c",
    "Margin__c",
    "Field_Maps_Prints_Complete_GIS__c",
    "SOF_Replacing_Status__c",
    "SOF_Replacing_Active_Flag__c",
    "Replacing_SOF_Status_Update_Flag__c",
    "Field_Maps_Prints_Approved_OSP__c",
    "Notes__c",
    "Address_verification_Status__c",
    "Sub_Contractor__c",
    "Temporary_Solution__c",
    "POP_Ready__c",
    "Operating_Area_Addr_A__c",
    "Operating_Area_Addr_Z__c",
    "Address_Verified__c",
    "Auto_Renew__c",
    "Estimated_Underground_Footage__c",
    "Dimension_1_Location__c",
    "Dimension_2_Line_of_Business__c",
    "FFA_Company__c",
    "Estimated_Aerial_Footage__c",
    "Pro_Rata_Billing__c",
    "Neustar_ICSC__c",
    "Neustar_AP_REP_TELNO__c",
    "POP_Ready_Date__c",
    "MTU_Address__c",
    "Total_Un_Invoiced_Amount__c",
    "Neustar_AP_REP__c",
    "Site_Name__c",
    "Adherence_As_Spliced_Verified_Bypass__c",
    "Billing_Cycle_Date__c",
    "Adherence_OTDR_Verified_Bypass__c",
    "Site_Name_Formula__c",
    "Adherence_Timely_As_Built_Import_Bypass__c",
    "Core_Eng_logical__c",
    "Fiber_Whip_Installation_Date__c",
    "Date_Project_Completed__c",
    "Design_Uploaded_Date__c",
    "ISP_Logical__c",
    "NOC_Logical__c",
    "No_Permitting_Required__c",
    "OSP_Engineer_Assigned_Date__c",
    "OTDR_Verified_Status__c",
    # Power_Location_Lat_Long__c excluded (compound location)
    "Service_Delivery_logical__c",
    "Total_Path__c",
    "OSP_Design_Complete_Due__c",
    "OSP_Design_Submit_Due__c",
    "Revenue_Booking_State__c",
    "Account_Active__c",
    "OSS_Service_ID__c",
    "Related_Order_Portability__c",
    "Billing_Invoice__c",
    "OSS_Order_is_Disco__c",
    "Is_Account_Owner__c",
    "Contract_End_Date_Est__c",
    "Notes_from_Sales_Person_Full__c",
    "Predecessor_Project__c",
    "Billing_Reference__c",
    "Site_Survey_Completed_Due__c",
    "Has_Successor__c",
    "Referring_Vendor_Agent__c",
    "Service_Order_Record_Type__c",
    "Sales_Rep__c",
    "Service_Term_Months_Est__c",
    "my_order__c",
    "Parent_SOF__c",
    "SBQQ__Contracted__c",
    "SBQQ__ContractingMethod__c",
    "SBQQ__PaymentTerm__c",
    "SBQQ__PriceCalcStatusMessage__c",
    "SBQQ__PriceCalcStatus__c",
    "SBQQ__Quote__c",
    "SBQQ__RenewalTerm__c",
    "SBQQ__RenewalUpliftRate__c",
    "SBQQ__OrderBookings__c",
    "SBQQ__TaxAmount__c",
    "Address_A__c",
    "Address_Z__c",
    "Quote_Line_Group__c",
    "Address_A_Link__c",
    "Address_Z_Link__c",
    "Site_Survey_Scheduled_Due__c",
    "Design_Upload_Status__c",
    "PDF_Document_Comments__c",
    "Design_Upload_Completed_Status__c",
    "Active_Pending_Disconnected__c",
    "Hidden_URL_Account__c",
    "Address_A_Contact__c",
    "Address_Z_Contact__c",
    "Order_Term__c",
    "Co_Term__c",
    "Sales_Rep_s_Manager__c",
    "Quote_Line__c",
    "On_Off_Net__c",
    "Sales_Rep_s_Manager_s_Manager__c",
    "Permits_Submitted__c",
    "Created_Date_Time__c",
    "Dimension_4_Market__c",
    "Backbone_Impacted__c",
    "TSP_Code_Value__c",
    "Address_A_Marked_On_Net__c",
    "Address_Z_Marked_On_Net__c",
    "OSP_Confirmation_Date__c",
    "Primary_Product_Name__c",
    "OSP_logical__c",
    "CRM_AM__c",
    "Customer_Requested_Due_Date_Override__c",
    "Permitting_Logical__c",
    "Cloned_from_Another_Record__c",
    "Data_Load_ID__c",
    "DO_NOT_Create_Sales_Commission__c",
    "Account_Industry_Segment__c",
    "Sales_Commission_Generated__c",
    "Address_Z_Reporting__c",
    "Address_A_Reporting__c",
    "Data_Load_Source__c",
    "DO_NOT_SYNC_To_Billing__c",
    "Initially_Activated_By__c",
    "Address_Z_Name__c",
    "Primary_Product_Family__c",
    "Account_Move__c",
    "Test_Running__c",
    "Service_End_Reasons__c",
    "ServiceEndSecondary_Reasons__c",
    "Bypass_Automatic_Template_Selection__c",
    "DO_NOT_Create_Project__c",
    "Program__c",
    "Project_Status__c",
    "Project_Group__c",
    "Estimated_Project_Completion_Date__c",
    "Estimated_Completion_Date__c",
    "Projected_Completion_Past_ECD__c",
    "Product_Family_Override__c",
    "Splice_Documents_Imported__c",
    "Aerial_Perrmit_Needed__c",
    "Cloud_Engineer_Needed__c",
    "Core_Design_Needed__c",
    "Customer_Design_Requirements__c",
    "DOT_Permit_needed__c",
    "New_Order_Comments__c",
    "Date_Project_Created__c",
    "Facilities_Needed__c",
    "ISP_Needed__c",
    "Leased_Conduit_Permit_Needed__c",
    "Neustar_Message_Types__c",
    "Lit_Building__c",
    "MSP_Engineer_Needed__c",
    "OSP_Needed__c",
    "Railroad_Permit_Needed__c",
    "Neustar_Supp_Requested__c",
    "Service_Delivery_Needed__c",
    "Small_Cell_Needed__c",
    "Template_Title__c",
    "Build_Plan_Year__c",
    "Transport_Needed__c",
    "Underground_Permit_Needed__c",
    "Adherence_Report_logical__c",
    "Voice_Needed__c",
    "Approved_Permits_Count__c",
    "CHILD_TOTAL_COUNT_PERMIT_NEW__c",
    "Status_Permit_Formula__c",
    "Status_Permit__c",
    "Total_Permits_Required__c",
    "PON__c",
    "Cloud_Engineer__c",
    "Core_Design_Engineer__c",
    "ECD_Change_Prior_Value__c",
    "ECD_Change_User__c",
    "ECD_Change_When__c",
    # Lines 382-583
    "Facilities_Engineer__c",
    "ISP_Engineer__c",
    "MSP_Engineer__c",
    "OSP_Engineer__c",
    "Service_Delivery_Manager__c",
    "Transport_Engineer__c",
    "Voice_Engineer__c",
    "BOM_fiber_optic_cable_total__c",
    "CHILD_OPEN_COUNT_DESIGN_NEW__c",
    "CHILD_OPEN_COUNT_PERMIT_NEW__c",
    "CHILD_TOTAL_COUNT_DESIGN_NEW__c",
    "Core_Design_Complete_NEW__c",
    "Permit_Count_Cancelled_NEW__c",
    "Permit_Exceptions_in_Review_NEW__c",
    "Permits_Count_of_New_With_Contractor_NEW__c",
    "Roll_Up_Core_Provisioning_Complete_NEW__c",
    "Roll_Up_Equipment_Provisioning_Compl_NEW__c",
    "Roll_Up_Noc_Provisioning_Complete_NEW__c",
    "Status_Design_Formula__c",
    "Status_Design__c",
    "SOF_Revenue_Value_Override__c",
    "Revenue_Value__c",
    "Reporting_Revenue__c",
    "Power_Approved_Date__c",
    "Power_Submitted_Date__c",
    "Scheduled_Installation_Date__c",
    "CCD_Change_Prior_Value__c",
    "CCD_Change_User__c",
    "Expansion_Engineer__c",
    "Fiber_Design_Engineer__c",
    "Fiber_Design_Engineer_Needed__c",
    "Expansion_Engineer_Needed__c",
    "OSP_Design_Due_Date__c",
    "Force_Project_Creation__c",
    "Alt_Site_Contact_Email__c",
    "Alt_Site_Contact_Phone__c",
    "Alt_Site_Contact__c",
    "Projected_Completion_Date_Beyond_ECD__c",
    "Power_Vendor__c",
    "Power_Meter_ID__c",
    "Build_Type_Address_A__c",
    "As_Built_Imported_GIS__c",
    "As_Built_Not_Needed_OSP__c",
    "As_Built_Uploaded_OSP__c",
    "GIS_Specialist_Needed__c",
    "GIS_Specialist__c",
    "SOF_Start_Date_After_End_Date__c",
    "Last_Order_Comment__c",
    "Expedite_Flag__c",
    "CCD_Change_When__c",
    "Do_NOT_Create_Design_Layout__c",
    "SDM_Searchable__c",
    "Reported_Disconnect_Date__c",
    "Create_Work_Order_Opp__c",
    "Project_Template_pl__c",
    "ECD_Month_Year__c",
    "Neustar_INIT__c",
    "Fiber_Design_Logical__c",
    "On_Air__c",
    "Wireless_Cutover_Date__c",
    "Service_Order_Agreement_Number__c",
    "E_rate_RHC__c",
    "SOF_MRC__c",
    "Related_Disconnect__c",
    "Churn_Override__c",
    "Churn__c",
    "Product_Code__c",
    "Issue_Category__c",
    "Final_Permit_Approved__c",
    "Last_Estimated_Permit_Approval_Date__c",
    "First_Permit_Submitted_Date__c",
    "Installation_Complete__c",
    "Last_Order_Comment_Date__c",
    "Primary_Product_Name_Override__c",
    "As_Built_Rejection__c",
    "Neustar_INIT_TELNO__c",
    "Service_Category_Multi__c",
    "Address_Z_Type_of_Building__c",
    "Legacy_Site_ID__c",
    "NOC_Disconnect_Complete__c",
    "Total_Vendor_MRC_Offnet_Heroku_Sync__c",
    "Customer_Project_ID__c",
    "Core_Disconnect__c",
    "Disconnect_Splice_Package_Completed__c",
    "Disconnect_Splicing_Completed__c",
    "Disconnect_Splicing_Docs_Uploaded__c",
    "Disconnect_Splicing_Required__c",
    "Soft_Disconnect_Date__c",
    "Transport_Disconnect__c",
    "Unassign_Fibers__c",
    "Show_Expedited_Banner__c",
    "Maintenance_Contact_Email__c",
    "Maintenance_Contact_Phone__c",
    "Maintenance_Contact__c",
    "Address_Z_LOA_CFA_Complete_Date__c",
    "Address_Z_LOA_CFA_Required__c",
    "Address_A_ISP_Engineer__c",
    "Address_A_OSP_Engineer__c",
    "Address_A_Fiber_Design_Engineer__c",
    "Service_ID_No_Spaces__c",
    "Site_Name_No_Spaces__c",
    "BBF_New_Id__c",
    "BOM_inside_building_material_total__c",
    "BOM_labor_inside_wiring_total__c",
    "BOM_labor_overhead_aerial_total__c",
    "BOM_labor_underground_total__c",
    "BOM_misc_total__c",
    "BOM_network_equipment_toal__c",
    "BOM_permitting_total__c",
    "BOM_utilities_make_ready_total__c",
    "Base_Map_Imported__c",
    "Base_Map_received__c",
    "Core_Provisioning_Complete_Date__c",
    "Construction_Completion_Date__c",
    "Construction_Materials_Total__c",
    "Construction_Status__c",
    "Contractor__c",
    "Customer_Touch_Jeopardy_Projects__c",
    "Customer_Touch_Point_On_Track_Projects__c",
    "Days_between_CCD_and_ECD__c",
    "Days_to_Order_Confirmation__c",
    "Design_Package_Status__c",
    "Design_Request_Received__c",
    "Designs_Completed_Date__c",
    "Facility__c",
    "Fast_Track__c",
    "Fiber_Optic_Cable_Total__c",
    "IRU_Access__c",
    "Fiber_Design_Complete_Date__c",
    "LL_Ntp_Received__c",
    "Design_Imported_GIS_Date__c",
    "Construction_Complete_Status_Date__c",
    "OSP_Task_logical__c",
    "ECD_then_BSD_Reporting__c",
    "All_Permits_Completed__c",
    "NTP_Request_Submitted__c",
    "Design_Layout_For_Formula__c",
    "OSPE_Walkout_Date__c",
    "OSP_DEsign_Imported__c",
    "OSP_DEsign_Received__c",
    "OSP_Design_Revised__c",
    "OSP_Notes__c",
    "OTDR_Complete__c",
    "OTDR_Distance__c",
    "OTDR_Loss__c",
    "Order_Confirmation_Sent_Date__c",
    "Order_Phase__c",
    "Permit_Approved__c",
    "ECD_Change_Counter__c",
    "Phase_Milestone_Fiber_Coiled_at_Curb__c",
    "IRU_Owner__c",
    "Project_Module__c",
    "Hold_Reason_Notes__c",
    "Quote_Vendor_Name__c",
    "Account_Link__c",
    "Site_Name_Address_A__c",
    "Selected_Headend_Type__c",
    "Site_Contact_Email__c",
    "Site_Contact_Phone__c",
    "Site_Contact_Preferred_Method__c",
    "Site_Contact__c",
    "Site_Contacted__c",
    "Site_Received__c",
    "Site_Survey_Complete__c",
    "Site_Survey_Scheduled__c",
    "Small_Cell_Contractor__c",
    "LOA_CFA_Required__c",
    "Splice_Documents_Received__c",
    "Status_ROE__c",
    "Utilities_Make_Ready_Total__c",
    "Walkout_Completed__c",
    "Wireless_Customer_NTP__c",
    "Wireless_Customer_Telco_Ready__c",
    "Wireless_Distance_from_fiber_feet__c",
    "Wireless_Entity__c",
    "Wireless_Joint_Virtual_Walkout_Complete__c",
    "Wireless_List_received__c",
    "Wireless_On_Net_Off_Net_Status__c",
    "Wireless_Polygon__c",
    "Wireless_Site_Design_Submitted__c",
    "Wireless_Site__c",
    "LOA_CFA_Complete_Date__c",
    "Wireless_Transport_Approval__c",
    "Customer_Comments_Last_Modified_Date__c",
    "Opportunity_Service_Category__c",
    "Opportunity_Stage__c",
    "Hold_Reason__c",
    "Address_A_Type_of_Building__c",
    "Confirmed_FOC_Date__c",
    "Target_FOC_Date__c",
    "ISP_Completion__c",
    "Projected_Telco_Ready__c",
    "Order_Confirmation_FOC__c",
    "Force_Resource_Sync__c",
    "Permits_Approved__c",
    "Order_Completion_Notice_Sent__c",
    "Pole_Build_Type__c",
    "Pole_Type__c",
    "Pole_Set_Date__c",
    "Pole_Request_Approved_Date__c",
    "Pole_Request_Submitted_Date__c",
]

# --- Address__c fields (all from es_Address__c_fields.csv minus compound types) ---
ADDRESS_FIELDS = [
    "Id",
    "OwnerId",
    "IsDeleted",
    "Name",
    "RecordTypeId",
    "CreatedDate",
    "CreatedById",
    "LastModifiedDate",
    "LastModifiedById",
    "SystemModstamp",
    "LastActivityDate",
    "LastViewedDate",
    "LastReferencedDate",
    "Active_Location__c",
    "Address_2__c",
    "Address_Last_Verified__c",
    "Address_Link__c",
    "Address_Return_Code__c",
    "Address_Status__c",
    "Address_Type_Formula__c",
    "Address_Type__c",
    "Address__c",
    "IsRunningTest__c",
    "City__c",
    "Clean_Street__c",
    "Combined_Fields__c",
    "Country__c",
    "County_FIPS__c",
    "County__c",
    # Geocode_Lat_Long__c excluded (compound location)
    "Headend__c",
    "Location_id__c",
    "NNI__c",
    "On_Net__c",
    "Organization__c",
    "Output_Document_Address__c",
    "Partial_Address_1__c",
    "State__c",
    "Unique_Constraint_Check__c",
    "Unique_Location_Search__c",
    "Unit__c",
    "Urbanization__c",
    "Vacant_Location__c",
    "Verification_Used__c",
    "Verified__c",
    "Zip__c",
    "GIS_Verified__c",
    "Nexus_ID__c",
    "Site_ID__c",
    "Fixed_Assets_Assigned__c",
    "Output_Document_Address_Without_Headend__c",
    "Output_Document_Address_With_Type__c",
    "Combined_Fields_One_Line__c",
    "Dimension_4_Market__c",
    "Partial_Address_1_Formula__c",
    "DMARC_Location__c",
    "Imported_ID__c",
    "Data_Load_ID__c",
    "Data_Load_Source__c",
    "Zip_5_Char__c",
    "Building_Status__c",
    "Building_Type_Details__c",
    "Building_Type__c",
    "Data_Axle_Build__c",
    "Geocoded__c",
    "Restricted_Reason_Details__c",
    "Restricted_Reason__c",
    "Footnotes__c",
    "GeoCoordinate_String__c",
    "Active_Job_ID__c",
    "Address_Precision__c",
    "Geocode_Precision__c",
    "Street_3__c",
    "Street_4__c",
    "RDI__c",
    "Zip_Plus_4__c",
    "Carrier_Route__c",
    "Barcode__c",
    "Time_Zone__c",
    "DST__c",
    "Do_Not_Verify__c",
    "Verified_By_User__c",
    "UTC_Offset__c",
    "Match_Details__c",
    "Area_Code_s__c",
    "Urban_Area_Code__c",
    "Urban_Area_Name__c",
    "Thoroughfare_Complete__c",
    "Thoroughfare_Name__c",
    "Administrative_Area__c",
    "Super_Admin_Area__c",
    "Sub_Building_Number__c",
    "Sub_Building_Type__c",
    "Premise__c",
    "Premise_Extra__c",
    "Address_Format__c",
    "Dependent_Locality__c",
    "Dependent_Locality_Name__c",
    "Post_Box__c",
    "Sub_Building__c",
    "Complete_Address__c",
    "Virtually_On_Net_VON__c",
    "Demand_Record__c",
    "Attempted_to_Link_to_Demand_Records__c",
    "Wholesale_Expanded_On_Net_Building__c",
    "CLLI__c",
    "Address_Used_by_an_SOF__c",
    "Site_Access_Notes__c",
    "Address_On_Completed_Project__c",
    "On_Completed_Project_Without_Status_Type__c",
    "Zip_is_Missing_Digits__c",
    "MTU__c",
    "Pre_Sale_Address__c",
    "MDU_DEMARC_Certified__c",
    "Building_Address_Parent__c",
    "Is_Parent__c",
    "Run_Batch_Verification__c",
    "Address_Match_Hierarchy__c",
    "Address_Match_Exclusion__c",
    "Address_Match_Key__c",
    "Is_Child_Address__c",
    "BBF_New_Id__c",
]

# --- Facility__c fields (all from es_Facility__c_fields.csv minus compound types) ---
FACILITY_FIELDS = [
    "Id",
    "OwnerId",
    "IsDeleted",
    "Name",
    "CreatedDate",
    "CreatedById",
    "LastModifiedDate",
    "LastModifiedById",
    "SystemModstamp",
    "LastActivityDate",
    "LastViewedDate",
    "LastReferencedDate",
    "Location__c",
    "Facility_Type__c",
    "SiteID__c",
    "Floor__c",
    "Room_Number__c",
    "Facility_Owner__c",
    "Common_Name__c",
    "Related_Network_Location_Address__c",
    "Site_Details__c",
    "Backbone_Facility__c",
    "Collocation_MRC__c",
    "Address__c",
    "AC_Power_Account_Number__c",
    "AC_Power_Availability__c",
    "AC_Power_Commercial_Provider__c",
    "AC_Power_Contact_Name__c",
    "AC_Power_Contact_Number__c",
    "AC_Power_Emergency_Contact_Info__c",
    "Alarm_Code__c",
    "Bathroom_Access__c",
    "Bathroom_Location__c",
    "CLLI_Code__c",
    "Cage_Access__c",
    "Cage_Floor__c",
    "Cage_Lockbox_Code__c",
    "Colocation_Type__c",
    "DC_Power_Plant_Battery_Strings__c",
    "DC_Power_Plant_Capacity__c",
    "DC_Power_Plant_Contact_Number__c",
    "DC_Power_Plant_Emergency_Number__c",
    "DC_Power_Plant_Load__c",
    "DC_Power_Plant_Maintenance_Vendor__c",
    "DC_Power_Plant_Make__c",
    "DC_Power_Plant_Vendor_Contact_Name__c",
    "Email_Address_For_Access__c",
    "Entrance_Door_Location__c",
    "Entrance_Notes__c",
    "Escorted_Access__c",
    "Exterior_Door_Access__c",
    "Exterior_Door_Code__c",
    "Facility_Address__c",
    "Facility_Docs_Link__c",
    # Facility_Geolocation__c excluded (compound location)
    "Fire_Protection_Contact_Name__c",
    "Fire_Protection_Contact_Number__c",
    "Fire_Protection_Emergency_Contact__c",
    "Gate_Access_Code__c",
    "Generator_Fuel_Type__c",
    "Generator_Owner__c",
    "Generator_Repair_Company_Info__c",
    "Generator_Size_Model__c",
    "HVAC_Maintenance_Contact_Number__c",
    "HVAC_Maintenance_Vendor_Contact_Name__c",
    "HVAC_Number_Of_Units__c",
    "HVAC_Size_Of_Units__c",
    "HVAC_Type__c",
    "Hours_Of_Access__c",
    "Interior_Door_Access__c",
    "Interior_Lockbox_Code__c",
    "Interior_Lockbox_Location__c",
    "Key_Lockbox_Code__c",
    "Key_Lockbox_Location__c",
    "Misc_Notes__c",
    "Number_of_Racks__c",
    "On_Site_Generator__c",
    "Last_PM_Completed__c",
    "PM_Last_Completed__c",
    "Parking_Locations__c",
    "Parking_Meters__c",
    "Parking_Notes__c",
    "Portal_Web_Address__c",
    "Rack_Drawing_Link__c",
    "Secondary_Site_Owner_Contact__c",
    "Secondary_Site_Owner_Email__c",
    "Secondary_Site_Owner_Number__c",
    "Security_Company__c",
    "Security_Contact_Info__c",
    "Site_Admin__c",
    "Site_Emergency_Contact_Info__c",
    "Site_Owner_Contact_Email__c",
    "Site_Owner_Contact_Name__c",
    "Site_Owner_Contact_Number__c",
    "Site_Photo_Link__c",
    "Suite_Cage_Num__c",
    "Ticket_Needed_Access__c",
    "Status__c",
    "Dimension_4_Market__c",
    "IT_Related__c",
    "Circuit_Type__c",
    "Circuit_Provider__c",
    "SOF_Number__c",
    "Service_ID__c",
    "Site_Validated__c",
    "Last_Audit_Date__c",
    "Data_Load_Source__c",
    "Data_Load_ID__c",
    "File_Count__c",
    "PMF__c",
    "Site_Restricted_do_not_design_to_site__c",
    "X100G_Ethernet_Capable_Requires_Upgrade__c",
    "X100G_Ethernet_Capable__c",
    "X100G_Wave_Capable_Requires_Upgrade__c",
    "X100G_Wave_Capable__c",
    "X10G_Ethernet_Capable_Requires_Upgrade__c",
    "X10G_Ethernet_Capable__c",
    "X10G_Wave_Capable_Requires_Upgrade__c",
    "X10G_Wave_Capable__c",
    "X1G_Ethernet_Capable__c",
    "X400G_EthernetCapable__c",
    "X400G_Ethernet_Capable_Requires_Upgrade__c",
    "X400G_Wave_Capable_Requires_Upgrade__c",
    "Location_ID__c",
    "Battery_Date_Code__c",
    "LAST_HVAC_PM__c",
    "Last_Fire_Sup__c",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def connect_to_salesforce():
    """Establish Salesforce connection using configured credentials."""
    # Check for session-based auth first
    session_id = globals().get("SESSION_ID", "")
    instance_url = globals().get("INSTANCE_URL", "")

    if session_id and instance_url:
        print("Connecting via existing session...")
        return Salesforce(session_id=session_id, instance_url=instance_url)

    if not SF_USERNAME or not SF_PASSWORD:
        print("ERROR: No credentials configured.")
        print("Edit the CONFIGURATION section at the top of this script.")
        sys.exit(1)

    print(f"Connecting as {SF_USERNAME} to {SF_DOMAIN}.salesforce.com...")
    try:
        sf = Salesforce(
            username=SF_USERNAME,
            password=SF_PASSWORD,
            security_token=SF_SECURITY_TOKEN,
            domain=SF_DOMAIN,
        )
        print("Connected successfully.")
        return sf
    except SalesforceAuthenticationFailed as e:
        print(f"ERROR: Authentication failed — {e}")
        sys.exit(1)


def query_all_records(sf, soql):
    """
    Execute a SOQL query and handle pagination (queryMore) automatically.
    Returns the full list of record dicts.
    """
    print(f"  Executing query ({len(soql)} chars)...")
    result = sf.query(soql)
    records = result["records"]
    total = result["totalSize"]
    print(f"  Total records matching: {total}")

    while not result["done"]:
        next_url = result["nextRecordsUrl"]
        result = sf.query_more(next_url, identifier_is_url=True)
        records.extend(result["records"])
        print(f"  Retrieved {len(records)} / {total}...")

    print(f"  Done — {len(records)} records retrieved.")
    return records


def records_to_csv(records, fields, filepath):
    """Write a list of Salesforce record dicts to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            # Remove the nested 'attributes' key that simple_salesforce adds
            row = {k: v for k, v in rec.items() if k != "attributes"}
            writer.writerow(row)
    print(f"  Saved {len(records)} rows to {filepath}")


def collect_lookup_ids(records, field_names):
    """
    Collect all non-null lookup IDs from the given fields across all records.
    Returns a deduplicated set.
    """
    ids = set()
    for rec in records:
        for field in field_names:
            val = rec.get(field)
            if val:
                ids.add(val)
    return ids


def chunk_list(lst, chunk_size):
    """Split a list into chunks of the given size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]


# =============================================================================
# MAIN EXTRACTION LOGIC
# =============================================================================


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 70)
    print(f"BBF Order Extract — {timestamp}")
    print("=" * 70)

    # --- Connect ---
    sf = connect_to_salesforce()

    # --- Step 1: Query Orders ---
    print("\n[1/3] Querying Orders...")
    order_field_str = ", ".join(ORDER_FIELDS)
    order_soql = (
        f"SELECT {order_field_str} "
        f"FROM Order "
        f"WHERE Status IN ('Activated', 'Suspended (Late Payment)', 'Disconnect in Progress') "
        f"AND (NOT Project_Group__c LIKE '%PA MARKET DECOM%') "
        f"AND Service_Order_Record_Type__c = 'Service Order Agreement' "
        f"AND Billing_Invoice__r.BBF_Ban__c = true"
    )
    order_records = query_all_records(sf, order_soql)

    if not order_records:
        print("No orders found matching the filter criteria. Exiting.")
        sys.exit(0)

    order_csv = os.path.join(OUTPUT_DIR, f"bbf_orders_{timestamp}.csv")
    records_to_csv(order_records, ORDER_FIELDS, order_csv)

    # --- Step 2: Query Related Addresses ---
    print("\n[2/3] Querying related Address__c records...")
    address_lookup_fields = ["Address_A__c", "Address_Z__c"]
    address_ids = collect_lookup_ids(order_records, address_lookup_fields)
    print(f"  Found {len(address_ids)} unique Address IDs from Orders.")

    all_address_records = []
    if address_ids:
        address_field_str = ", ".join(ADDRESS_FIELDS)
        # SOQL IN clause has a limit of ~20,000 chars / ~roughly 300-400 IDs
        # We chunk by 200 IDs to be safe
        address_id_list = sorted(address_ids)
        for i, chunk in enumerate(chunk_list(address_id_list, 200)):
            id_str = "', '".join(chunk)
            addr_soql = (
                f"SELECT {address_field_str} "
                f"FROM Address__c "
                f"WHERE Id IN ('{id_str}')"
            )
            print(f"  Address query batch {i + 1}...")
            batch = query_all_records(sf, addr_soql)
            all_address_records.extend(batch)

    address_csv = os.path.join(OUTPUT_DIR, f"bbf_addresses_{timestamp}.csv")
    records_to_csv(all_address_records, ADDRESS_FIELDS, address_csv)

    # --- Step 3: Query Related Facilities (from Orders AND Addresses) ---
    print("\n[3/3] Querying related Facility__c records...")
    facility_field_str = ", ".join(FACILITY_FIELDS)
    all_facility_records = []

    # 3a: Facilities referenced directly by Order lookup fields
    facility_lookup_fields = [
        "Facility__c",
        "Facility_address_z_a__c",
        "Facility_Address_Z_b__c",
    ]
    facility_ids_from_orders = collect_lookup_ids(order_records, facility_lookup_fields)
    print(
        f"  Found {len(facility_ids_from_orders)} unique Facility IDs from Order lookup fields."
    )

    if facility_ids_from_orders:
        fac_id_list = sorted(facility_ids_from_orders)
        for i, chunk in enumerate(chunk_list(fac_id_list, 200)):
            id_str = "', '".join(chunk)
            fac_soql = (
                f"SELECT {facility_field_str} "
                f"FROM Facility__c "
                f"WHERE Id IN ('{id_str}')"
            )
            print(f"  Facility (from Order lookups) batch {i + 1}...")
            batch = query_all_records(sf, fac_soql)
            all_facility_records.extend(batch)

    # 3b: Facilities where Address__c matches any of our collected Address IDs
    if address_ids:
        print(
            f"  Querying Facilities by Address__c relationship ({len(address_ids)} Address IDs)..."
        )
        addr_id_list = sorted(address_ids)
        for i, chunk in enumerate(chunk_list(addr_id_list, 200)):
            id_str = "', '".join(chunk)
            fac_soql = (
                f"SELECT {facility_field_str} "
                f"FROM Facility__c "
                f"WHERE Address__c IN ('{id_str}')"
            )
            print(f"  Facility (from Address__c) batch {i + 1}...")
            batch = query_all_records(sf, fac_soql)
            all_facility_records.extend(batch)

    # 3c: Facilities where SOF_Number__c matches any of our Order IDs
    order_ids = [rec.get("Id") for rec in order_records if rec.get("Id")]
    if order_ids:
        print(
            f"  Querying Facilities by SOF_Number__c relationship ({len(order_ids)} Order IDs)..."
        )
        for i, chunk in enumerate(chunk_list(sorted(order_ids), 200)):
            id_str = "', '".join(chunk)
            fac_soql = (
                f"SELECT {facility_field_str} "
                f"FROM Facility__c "
                f"WHERE SOF_Number__c IN ('{id_str}')"
            )
            print(f"  Facility (from SOF_Number__c) batch {i + 1}...")
            batch = query_all_records(sf, fac_soql)
            all_facility_records.extend(batch)

    # Count unique vs total (informational only — we keep all rows including dupes)
    unique_fac_ids = {rec.get("Id") for rec in all_facility_records if rec.get("Id")}
    print(
        f"  Total Facility rows collected: {len(all_facility_records)} "
        f"({len(unique_fac_ids)} unique IDs)"
    )

    facility_csv = os.path.join(OUTPUT_DIR, f"bbf_facilities_{timestamp}.csv")
    records_to_csv(all_facility_records, FACILITY_FIELDS, facility_csv)

    # --- Summary ---
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"  Orders:     {len(order_records):>6} records → {order_csv}")
    print(f"  Addresses:  {len(all_address_records):>6} records → {address_csv}")
    print(
        f"  Facilities: {len(all_facility_records):>6} records ({len(unique_fac_ids)} unique) → {facility_csv}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
