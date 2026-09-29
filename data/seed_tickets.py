"""
Creates and seeds the SQLite tickets database with sample case tickets.
Run once: python data/seed_tickets.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tickets.db")

TICKETS = [
    ("TK-001", "connectivity", "No internet access", "Customer reports complete loss of mobile internet after switching from 3G to 4G mode.", "Guided customer to toggle airplane mode and reset APN settings. Internet restored after APN was reset to default (internet.telecom.example).", "resolved"),
    ("TK-002", "connectivity", "Intermittent signal drops", "Customer in a suburban area experiences signal dropping to zero several times per day, affecting both calls and data.", "Network team identified a faulty sector antenna on the nearest tower. Temporary fix applied remotely; full hardware replacement scheduled within 48 hours. Customer offered 500 MB data compensation.", "resolved"),
    ("TK-003", "data", "Data balance not updating", "Customer purchased a 5 GB add-on pack but the balance still shows the old figure in the app.", "Billing system had a 30-minute sync delay. Refreshed the customer's session token via backend. Balance updated correctly after cache clear.", "resolved"),
    ("TK-004", "roaming", "Unexpected roaming charges", "Customer returned from a trip to Spain and received a bill $240 higher than expected. Claims they had a roaming bundle active.", "Investigated and found the roaming bundle was activated 3 hours after the customer's first data session abroad. Charges prior to bundle activation were billed at standard rates. Offered 50% goodwill credit ($30) on the pre-bundle charges.", "resolved"),
    ("TK-005", "sim", "SIM card not recognised after phone update", "Customer updated their Android phone and immediately got a 'SIM not provisioned' error.", "Soft-provisioned the SIM remotely via the BSS. Error resolved within 10 minutes without customer needing to visit a store.", "resolved"),
    ("TK-006", "billing", "Double charged for monthly plan", "Customer's bank statement shows two identical charges of $45 on the same date.", "Duplicate charge caused by a payment gateway retry during a network timeout. Confirmed only one payment received on our side. Issued a refund of $45 within 3–5 business days and sent confirmation email.", "resolved"),
    ("TK-007", "voice", "Calls going straight to voicemail", "All incoming calls reach voicemail immediately even though the phone shows full signal and is not on Do Not Disturb.", "Call barring had been activated on the account without the customer's knowledge. Deactivated call barring remotely via the HLR. Advised customer to set a new call barring PIN.", "resolved"),
    ("TK-008", "connectivity", "Extremely slow 4G speeds (below 1 Mbps)", "Customer's speed test consistently shows 0.3–0.8 Mbps download on 4G in a city centre location.", "Identified the local cell as congested during peak hours (5–8 pm). Enabled carrier aggregation on the customer's profile to utilise a secondary band. Speeds improved to 12–18 Mbps in follow-up test.", "resolved"),
    ("TK-009", "sim", "eSIM activation failing", "Customer purchased an iPhone 15 and is unable to complete eSIM activation — the QR code scan fails each time.", "QR code had a single-use expiry that was triggered during a failed attempt. Generated a fresh eSIM provisioning code via the eSIM portal and emailed it to the customer. Activation succeeded on second attempt.", "resolved"),
    ("TK-010", "billing", "Unable to view itemised bill", "Customer cannot download the PDF bill — the download button spins indefinitely.", "Known bug in the web portal affecting accounts with more than 500 itemised events per cycle. Sent the itemised bill manually as a password-protected PDF via email as a workaround. Escalated the portal bug to the engineering team.", "resolved"),
    ("TK-011", "device", "Phone not compatible with VoLTE", "Customer's new handset shows voice calls on 3G even though the SIM and plan support VoLTE.", "Checked the device IMEI against the VoLTE whitelist — handset model was a parallel import not on the approved list. Explained the limitation and offered an upgrade deal. Customer declined and accepted the 3G voice fallback.", "resolved"),
    ("TK-012", "roaming", "No service while abroad in Japan", "Customer with international roaming enabled has no signal at all while in Tokyo.", "Customer's plan had roaming enabled for Europe only. Extended roaming permissions to include Asia-Pacific region. Service restored within 15 minutes. Added a Japan daily bundle at customer's request.", "resolved"),
    ("TK-013", "account", "Cannot log in to the MyTelecom app", "Customer forgot their password and the reset email is not arriving.", "Reset email was going to the customer's old email address on file. Verified identity via security questions, updated email address, and manually triggered the password reset. Customer logged in successfully.", "resolved"),
    ("TK-014", "data", "Hotspot not working on unlimited plan", "Customer's unlimited plan should include hotspot but tethering is blocked by their device.", "The plan's hotspot feature requires a specific APN configuration for tethering. Sent step-by-step APN settings for the customer's Android device. Hotspot functional after settings update.", "resolved"),
    ("TK-015", "connectivity", "Network outage affecting whole street", "Multiple customers on the same street report total loss of service since 6 am.", "Major fibre backhaul cut reported by the field team at a junction box 2 km from the affected area. Repair crew dispatched; ETA 4 hours. Affected customers sent proactive SMS update. Service restored after 3 hours 20 minutes.", "resolved"),
    ("TK-016", "billing", "Plan auto-renewed at wrong price", "Customer's plan renewed at $55 instead of the promotional rate of $40 they signed up for.", "Promotional pricing period had expired per the original 12-month contract terms. Customer was unaware. As a goodwill gesture, applied the $40 rate for one additional month and advised the customer to check promotional expiry dates in the app.", "resolved"),
    ("TK-017", "voice", "Echo on every call", "Customer hears their own voice echoed back with a 1-second delay on all outgoing calls.", "Echo caused by a misconfigured echo cancellation setting on the local RNC. Reconfigured remotely. Customer confirmed echo resolved on a test call.", "resolved"),
    ("TK-018", "sim", "Number port taking too long", "Customer submitted a port-in request 6 hours ago and the number is still active on the old provider.", "Old provider had placed an admin hold on the number due to an outstanding balance. Advised customer to settle the balance with the old provider. Port completed within 1 hour of balance clearance.", "resolved"),
    ("TK-019", "data", "Background apps consuming all mobile data", "Customer used 8 GB of data in 3 days and believes their apps are syncing in the background without consent.", "Reviewed data usage breakdown — a cloud backup app had uploaded 6.2 GB. Educated customer on restricting background data per app in Android settings. Enabled Data Saver mode on the account as a safeguard.", "resolved"),
    ("TK-020", "account", "Unauthorised plan change on account", "Customer noticed their plan was downgraded from $60 to $30 without their authorisation.", "Audit log shows the change was made via the self-service portal from an unrecognised IP. Suspected account compromise. Reset credentials, enabled 2-factor authentication, reversed the plan change, and filed a security incident report.", "escalated"),
]

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS tickets")
    cur.execute("""
        CREATE TABLE tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id   TEXT UNIQUE NOT NULL,
            category    TEXT NOT NULL,
            issue_type  TEXT NOT NULL,
            description TEXT NOT NULL,
            resolution  TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'resolved'
        )
    """)

    cur.executemany(
        "INSERT INTO tickets (ticket_id, category, issue_type, description, resolution, status) VALUES (?,?,?,?,?,?)",
        TICKETS,
    )

    conn.commit()
    conn.close()
    print(f"Seeded {len(TICKETS)} tickets into {DB_PATH}")

if __name__ == "__main__":
    seed()
