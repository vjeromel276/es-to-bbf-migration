import logging
from simple_salesforce import Salesforce

# Sentry Logging
logging.basicConfig(level=logging.WARN)
logger = logging.getLogger("push-payables")

ES_USERNAME = "sfdcapi@everstream.net"
ES_PASSWORD = "pV4CAxns8DQtJsBq!"
ES_TOKEN = "r1uoYiusK19RbrflARydi86TA"
ES_DOMAIN = "login"

sf = Salesforce(
    username=ES_USERNAME,
    password=ES_PASSWORD,
    security_token=ES_TOKEN,
    domain=ES_DOMAIN,
)

companies = ["Everstream Ohio", "Everstream Michigan", "OneCommunity", "1C Corporation"]

for company in companies:
    sf.apexecute("FFACompany", method="POST", data={"companyName": company})
    sf.apexecute("VendorInvoicePin", method="PUT")
