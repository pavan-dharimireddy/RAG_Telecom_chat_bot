"""
Generates data/telecom_guide.pdf  - a multi-page Telecom Technical Reference Guide.
Run once: python data/generate_pdf.py
"""
import os
from fpdf import FPDF

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "telecom_guide.pdf")

SECTIONS = [
    (
        "1. Introduction to Mobile Networks",
        """Mobile networks have evolved through several generations, each offering significant improvements in speed, capacity, and capability.

2G (GSM) networks introduced digital voice and basic data services such as SMS. Data speeds were limited to around 50 kbps, sufficient only for text messaging and simple email.

3G (UMTS/HSPA) networks brought mobile broadband, enabling video calls, mobile internet browsing, and app downloads at speeds of 1-14 Mbps. This generation established the foundation for smartphone adoption worldwide.

4G (LTE) networks delivered a major leap forward, with typical download speeds of 20-150 Mbps and latency below 50 ms. LTE networks are fully IP-based, meaning voice calls are transmitted as data (VoLTE) rather than over a separate circuit-switched channel. LTE-Advanced (LTE-A) uses carrier aggregation to combine multiple frequency bands, pushing speeds beyond 300 Mbps.

5G networks represent the current frontier. Deploying across sub-6 GHz and millimetre-wave (mmWave) spectrum, 5G targets peak speeds of 10 Gbps, latency under 1 ms, and the ability to connect up to one million devices per square kilometre. This density makes 5G critical for IoT deployments, autonomous vehicles, and smart city infrastructure.

Network coverage depends on the frequency band used. Lower frequencies (700 MHz, 800 MHz) travel farther and penetrate buildings better but carry less data. Higher frequencies (2.6 GHz, mmWave) carry more data but have shorter range and are blocked more easily by walls and obstacles. Modern networks use a combination of bands to balance coverage and capacity.""",
    ),
    (
        "2. Troubleshooting Connectivity Issues",
        """Connectivity problems are the most common category of customer complaints. A structured diagnostic approach resolves the majority of cases without escalation.

Step 1  - Verify signal strength. Open the device's status bar or dial *3001#12345#* (iOS) or use a network signal app (Android) to view the raw signal level in dBm. A signal above -85 dBm is good; between -85 and -100 dBm is marginal; below -100 dBm is poor. If signal is weak, moving closer to a window or to a higher floor often helps.

Step 2  - Rule out a temporary network glitch. Toggle airplane mode on for 10 seconds then off. This forces the device to re-register on the network, which resolves many transient issues.

Step 3  - Check APN settings. The Access Point Name (APN) tells the device how to connect to the carrier's data network. Incorrect APN settings are a common cause of data connectivity failure after a phone reset or SIM swap. Navigate to Settings > Mobile Network > APN and verify the APN name, username, and password match the carrier's published settings.

Step 4  - Inspect the SIM. Power off the device, remove the SIM, clean the gold contacts with a dry cloth, and reseat it firmly. A partially seated SIM can cause intermittent connectivity.

Step 5  - Check for a network outage. Consult the carrier's live status page or app. If an outage is confirmed, no device-level action will restore service; the customer must wait for resolution.

Step 6  - Test with another SIM or device. Swapping the SIM into a different handset confirms whether the issue is with the SIM/network or the device hardware. A faulty antenna or damaged SIM slot requires device repair.

Step 7  - Escalate. If steps 1-6 do not resolve the issue, raise a network investigation ticket with the customer's location coordinates, affected time windows, and device model. The network operations team will perform a remote cell analysis.""",
    ),
    (
        "3. Understanding Data Plans and Fair Use Policy",
        """Data plans define how much high-speed data a customer can consume per billing cycle. Understanding plan mechanics helps agents resolve billing disputes and set correct customer expectations.

High-Speed Data Allowance: Each plan includes a fixed high-speed data allowance (e.g. 20 GB, 50 GB, or Unlimited). Once this allowance is consumed, the account is throttled to a reduced speed  - typically 512 kbps on standard plans and 1 Mbps on premium plans  - for the remainder of the billing cycle. Throttled speeds allow continued internet use but are unsuitable for video streaming or large downloads.

Unlimited Plans and Fair Use: Plans marketed as "unlimited" are subject to a Fair Use Policy (FUP). Customers who consume an unusually large volume of data  - typically above 100 GB per cycle  - may be deprioritised during periods of network congestion. Deprioritisation is temporary and only applied when the customer is connected to a congested cell; it does not affect customers in uncongested areas.

Data Rollover: Some plans include a data rollover feature. Unused high-speed data at the end of a billing cycle is carried forward to the next cycle, up to a maximum of one month's allowance. Rolled-over data is consumed before the current cycle's allowance.

Add-On Data Packs: Customers who exhaust their high-speed allowance mid-cycle can purchase add-on data packs to restore full speeds. Packs activate immediately upon purchase and are valid until the end of the current billing cycle. Unused add-on data does not roll over.

Hotspot (Tethering) Usage: Hotspot usage draws from the same data allowance as device usage. However, some plans include a separate hotspot sub-allowance. Once the hotspot sub-allowance is exhausted, hotspot speeds are throttled even if device data remains available. Enterprise and business plans typically have higher or uncapped hotspot allowances.

Data Usage Monitoring: Customers can monitor real-time usage in the MyTelecom app. Push notifications are sent at 80% and 100% of usage. Enabling data usage alerts at the OS level provides an additional safeguard against unexpected overages.""",
    ),
    (
        "4. International Roaming  - How It Works",
        """When a customer travels outside the home network's coverage area, their device connects to a partner network in the visited country. This is called roaming. Understanding the roaming architecture helps agents diagnose roaming failures and billing issues.

Technical Mechanism: The visited network authenticates the customer via an inter-operator signalling protocol (SS7 or Diameter). The home network validates the subscription and authorises service. All data, voice, and SMS traffic is tunnelled back to the home network for billing. This tunnelling adds latency compared to local network usage.

Roaming Zones: Our network divides the world into roaming zones based on inter-operator agreements and cost structures. Zone A (EU, UK, Australia, New Zealand) has the lowest roaming rates. Zone B (USA, Canada, Japan, Singapore) has moderate rates. Zone C (Rest of World) has the highest per-MB and per-minute charges. Customers should always purchase a roaming bundle before travelling to Zone B or C countries to avoid bill shock.

Activating Roaming: Roaming must be enabled on the account before departure. The customer can toggle it in the MyTelecom app under Plan & Services > International Roaming or by calling 611. Network-level activation takes up to 15 minutes. If a customer enables roaming after landing abroad, they may receive a brief period of no service while the HLR record is updated.

Roaming Bundles: Bundles are purchased for a specific destination or zone and are valid for the calendar days selected. A daily bundle covers midnight to midnight in the home timezone. Customers who activate a bundle after using some data on the day will still be charged the bundle price, but any pre-bundle usage at standard rates is not reversed.

Common Roaming Failures: The three most common reasons a customer has no service abroad are: (1) roaming not enabled on the account, (2) device not configured for automatic network selection  - navigate to Settings > Mobile Network > Network Selection > Automatic, (3) the visited country is not covered by our roaming agreements. Always check the coverage map before travel.

Steering of Roaming: In some countries, multiple partner networks are available. Our network steers customers to the preferred partner using priority lists in the SIM. If the preferred network is congested or unavailable, the SIM will attempt the next network on the list. Manual network selection in the device settings overrides steering.""",
    ),
    (
        "5. SIM Card Technology",
        """The Subscriber Identity Module (SIM) is the secure element that identifies a customer on the network. It stores the International Mobile Subscriber Identity (IMSI), authentication keys, and basic service configuration.

Form Factors: SIM cards have evolved from the original credit-card-sized (1FF) format through mini-SIM (2FF), micro-SIM (3FF), and nano-SIM (4FF). Today the vast majority of smartphones use nano-SIM. Some industrial IoT devices still use the larger 2FF format for robustness.

eSIM: The embedded SIM (eSIM) is a chip soldered directly into the device during manufacture. Unlike a physical SIM it can be reprogrammed over the air. The customer receives a QR code or activation code that loads a profile onto the eSIM. eSIM supports multiple profiles simultaneously, allowing the user to switch between carriers or maintain a local SIM while roaming without physically swapping cards. Most flagship smartphones since 2020 support eSIM.

iSIM: The integrated SIM (iSIM) goes a step further by integrating the SIM functionality directly into the device's main SoC (System-on-Chip). iSIM reduces device size and power consumption further than eSIM and is common in smartwatches and IoT devices.

SIM Security: The SIM stores Ki, a 128-bit authentication key that never leaves the card. During network authentication, the network and SIM independently compute a response to a random challenge using Ki and the MILENAGE algorithm. This mutual authentication prevents cloning and man-in-the-middle attacks. SIM PINs provide an additional layer of protection; after three incorrect PIN attempts the SIM is locked and requires a PUK code to unlock.

SIM Swap Fraud: SIM swap attacks occur when a fraudster convinces a carrier to transfer a victim's number to a new SIM. This allows the attacker to intercept SMS-based two-factor authentication messages. Agents must follow strict identity verification procedures before processing any SIM replacement request. In-store requests require government-issued photo ID. Remote requests require multi-factor identity confirmation.""",
    ),
    (
        "6. VoLTE, VoWiFi, and Advanced Voice Services",
        """Voice over LTE (VoLTE) and Voice over Wi-Fi (VoWiFi) are IP-based voice technologies that replace the legacy circuit-switched voice channel used in 2G and 3G networks.

VoLTE: With VoLTE, voice calls are transmitted as data packets over the LTE network using the IMS (IP Multimedia Subsystem) core. Benefits include HD voice quality (wideband audio at 16 kHz versus the 3.4 kHz of legacy calls), faster call setup times (under 2 seconds versus 6-8 seconds on 3G), and the ability to use data and voice simultaneously without degradation. VoLTE requires a compatible device, a VoLTE-enabled SIM, and an account that has VoLTE activated.

Enabling VoLTE: On most Android devices navigate to Settings > Mobile Network > VoLTE and toggle it on. On iPhone go to Settings > Mobile Data > Mobile Data Options > Voice & Data and select LTE. If the option is absent the device may not support VoLTE or the profile has not been pushed to the SIM. Agents can push the VoLTE profile remotely via the subscriber management system.

VoWiFi (Wi-Fi Calling): VoWiFi extends IMS calling over any Wi-Fi network, including home broadband and public hotspots. This is especially valuable in areas with poor indoor cellular coverage. Calls seamlessly hand off between Wi-Fi and cellular as the customer moves, without dropping. Emergency calls over VoWiFi require the customer to register a fixed address for location purposes.

Quality of Service: IMS networks apply Quality of Service (QoS) markings to voice packets, ensuring they are prioritised over general data traffic. This prevents voice quality degradation during periods of network congestion. Without QoS, voice packets would compete with video streaming and file downloads, causing jitter and packet loss.

Fallback Behaviour: If a VoLTE call cannot be established  - for example, because the called party is on a network that does not support VoLTE interconnect  - the network automatically falls back to a 3G circuit-switched call. This fallback is transparent to the customer but results in lower audio quality and the loss of simultaneous data capability.""",
    ),
    (
        "7. Billing System Architecture and Common Disputes",
        """Understanding how the billing system works helps agents identify the root cause of billing disputes quickly and accurately.

Event-Based Billing: Every billable event  - a phone call, an SMS, a data session  - generates a Call Detail Record (CDR) at the network element (e.g. the GGSN for data, the MSC for voice). CDRs are streamed to the mediation layer, which normalises and enriches them before passing them to the billing engine. The billing engine applies the customer's rate plan to calculate the charge and posts it to the account ledger.

Billing Cycle: Each customer has a monthly billing cycle anchored to their account creation date. At the end of the cycle, the billing engine aggregates all charges, applies any discounts or bundle credits, and generates the invoice. Autopay customers are charged automatically 14 days after invoice generation.

Prepaid vs Postpaid: Prepaid accounts are charged in real time  - before each call or data session, the system checks the account balance and rejects the session if insufficient credit exists. Postpaid accounts accrue charges throughout the cycle and are billed at the end. Hybrid prepaid-postpaid plans (e.g. pay-monthly with real-time data top-ups) use a combination of both mechanisms.

Common Dispute Types and Resolutions:
 - Duplicate charges: Caused by payment gateway retries during network timeouts. The billing engine should detect duplicates via idempotency keys; if not, the agent must manually reverse the extra charge.
 - Roaming overcharges: Usually occur when a bundle was not active for the full roaming period. The itemised bill shows the exact timestamp of bundle activation versus the first roaming event.
 - Premium SMS subscriptions: Third-party services can charge customers via the carrier's billing system (Direct Carrier Billing). Customers sometimes subscribe inadvertently via a web click-to-subscribe. Agents can view and cancel all active DCB subscriptions in the subscriber management system.
 - Plan change billing: Mid-cycle plan upgrades are charged on a pro-rata basis from the change date. Downgrades take effect at the next cycle start. Customers sometimes misunderstand this and expect an immediate credit.

Bill Shock Prevention: The system sends automated alerts at 80% and 100% of plan allowances and when roaming charges exceed $20, $50, and $100 thresholds. Agents should verify that alerts are enabled on the account when handling a bill shock complaint.""",
    ),
    (
        "8. Network Security and Fraud Prevention",
        """Telecom networks are high-value targets for fraud. Agents play a critical role in the first line of defence.

SS7 and Diameter Vulnerabilities: The inter-operator signalling protocols (SS7 for 2G/3G and Diameter for 4G) were designed for trusted networks and have well-known vulnerabilities. Attackers with access to SS7 can intercept SMS messages (undermining SMS-based 2FA), track device location, and redirect calls. Carriers mitigate this with SS7 firewalls and anomaly detection systems, but the risk cannot be fully eliminated on legacy protocols. 5G's use of HTTPS-based APIs (Service Based Architecture) substantially reduces this attack surface.

SIM Swap Fraud: Described in Section 5. Key mitigation: enforce strict in-person or multi-factor remote identity verification before any SIM replacement. Flag accounts with recent SIM swaps for elevated fraud monitoring for 30 days.

International Revenue Share Fraud (IRSF): Fraudsters compromise a PBX or customer account and generate large volumes of calls to premium-rate international numbers, earning a revenue share from the terminating carrier. Signs include sudden spikes in international call volume, calls to unusual destinations, and calls at atypical hours. Automated fraud management systems flag and temporarily bar suspected accounts. Agents should not manually unbar flagged accounts without fraud team approval.

Wangiri (One-Ring) Scam: Fraudsters make calls that ring once and hang up. The victim calls back out of curiosity and is connected to a premium-rate number. Educating customers not to call back unknown international numbers reduces exposure.

Account Takeover: Attackers use credentials obtained from data breaches to log in to the MyTelecom app and make unauthorised changes (plan downgrades, SIM swaps, address changes for redirect scams). Mitigations include: mandatory 2FA for account changes, anomaly detection for logins from new devices or geographies, and step-up authentication for high-risk actions.

Data Privacy: Customer records are subject to data protection regulations. Agents must verify caller identity before disclosing any account information. The minimum required verification is the account holder's full name, date of birth, and either the account password or the last four digits of the payment card on file.""",
    ),
]


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Telecom Technical Reference Guide  - Internal Use Only", align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def build_pdf(output_path: str):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 20, 15)

    # Title page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 80, 160)
    pdf.ln(30)
    pdf.multi_cell(0, 12, "Telecom Technical\nReference Guide", align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 8, "Customer Care & Network Operations Edition", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(0, 6, "Version 3.2  |  Covers 2G / 3G / 4G LTE / 5G", align="C")

    # Sections
    for title, body in SECTIONS:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 80, 160)
        pdf.multi_cell(0, 9, title)
        pdf.ln(3)
        pdf.set_draw_color(30, 80, 160)
        pdf.set_line_width(0.5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 6, body)

    pdf.output(output_path)
    print(f"PDF written to {output_path}  ({pdf.page} pages)")


if __name__ == "__main__":
    build_pdf(OUTPUT_PATH)
