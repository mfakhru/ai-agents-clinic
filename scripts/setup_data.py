import os
import sys
import json
import sqlite3

from google import genai
from google.genai import types

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)
EMBEDDING_MODEL = 'gemini-embedding-001'

# Verify required environment variables
required_vars = ['GOOGLE_API_KEY']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Expected .env file location: {env_path}", file=sys.stderr)
    if not env_path.exists():
        print(f"✗ File not found at that location", file=sys.stderr)
    else:
        print(f"✓ File exists but is missing the variables above", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Make sure your .env file contains:", file=sys.stderr)
    for var in missing_vars:
        print(f"  {var}=<value>", file=sys.stderr)
    sys.exit(1)

# Local SQLite database path
DB_PATH = os.environ.get('DB_PATH', str(Path(__file__).parent.parent / 'database' / 'clinic.db'))

# Dental clinic services data
# Columns: (name, service_category, appointment_type, duration, price, tags, available, description)
CLINIC_SERVICES = [
    ("Scaling & Polishing", "Preventive", "Routine",
     "45 minutes",
     "$80", "Insurance Eligible, Child-Friendly", True,
     "Professional removal of plaque and tartar build-up above and below the gum line using ultrasonic scalers and hand instruments, followed by polishing to remove surface stains. Recommended every 6 months to prevent gum disease and maintain oral hygiene."),
    ("Deep Scaling (Root Planing)", "Periodontic", "Specialized",
     "60–90 minutes",
     "$200", "Insurance Eligible, Requires Anesthesia", True,
     "A non-surgical treatment for gum disease that involves thorough cleaning of the tooth roots to remove tartar and bacteria below the gum line. Local anesthesia is applied for comfort. Often done in two sessions covering upper and lower arches separately."),
    ("Teeth Whitening (In-Chair)", "Cosmetic", "Specialized",
     "60 minutes",
     "$350", "Cosmetic Only, Painless", True,
     "Professional-grade hydrogen peroxide gel activated by a LED light to break down deep stains and discoloration. Achieves up to 8 shades lighter in a single session. Results last 12–18 months with good oral hygiene. Take-home trays included for maintenance."),
    ("Dental X-Ray (Periapical / Panoramic)", "Diagnostic", "Routine",
     "15 minutes",
     "$50", "Insurance Eligible, Child-Friendly", True,
     "Digital radiographic imaging to detect cavities, bone loss, impacted teeth, and other issues invisible to the naked eye. Periapical X-rays focus on individual teeth while panoramic X-rays provide a full-mouth view. Low-radiation digital sensors are used."),
    ("Composite Filling", "Restorative", "Routine",
     "45 minutes",
     "$120", "Insurance Eligible", True,
     "Tooth-colored resin material used to restore teeth damaged by decay or minor fractures. The decayed portion is removed, and the composite is applied in layers and cured with UV light. Matches the natural tooth shade for an invisible, durable repair."),
    ("Root Canal Treatment", "Restorative", "Specialized",
     "90 minutes",
     "$800", "Insurance Eligible, Requires Anesthesia", True,
     "Endodontic treatment to save a severely infected or damaged tooth by removing the infected pulp, cleaning and shaping the root canals, and sealing them with biocompatible material. Typically followed by crown placement. Eliminates tooth pain and prevents extraction."),
    ("Dental Crown", "Restorative", "Specialized",
     "2 visits, 60 minutes each",
     "$1,200", "Insurance Eligible", True,
     "A custom-fitted porcelain or zirconia cap placed over a damaged, decayed, or root-canal-treated tooth to restore shape, strength, and appearance. The tooth is prepared on the first visit and a temporary crown fitted; the permanent crown is bonded on the second visit."),
    ("Dental Implant", "Surgical", "Specialized",
     "Multiple visits over 3–6 months",
     "$3,000", "Requires Anesthesia, Premium Service", True,
     "A titanium post surgically placed into the jawbone to replace a missing tooth root. After osseointegration (3–6 months), a custom abutment and porcelain crown are attached. Implants look, feel, and function like natural teeth and can last a lifetime with proper care."),
    ("Simple Tooth Extraction", "Surgical", "Routine",
     "30 minutes",
     "$150", "Insurance Eligible, Requires Anesthesia", True,
     "Removal of a fully erupted tooth using local anesthesia and dental forceps. Indicated for severely decayed, fractured, or loose teeth that cannot be saved. Post-extraction care instructions and gauze are provided. Healing typically takes 3–7 days."),
    ("Wisdom Tooth Removal", "Surgical", "Specialized",
     "60 minutes",
     "$400", "Insurance Eligible, Requires Anesthesia", True,
     "Surgical extraction of partially or fully impacted third molars causing pain, infection, or crowding. Performed under local anesthesia with optional sedation. The gum is incised and the tooth sectioned for safe removal. Recovery takes 5–7 days with prescribed medication."),
    ("Dental Veneer", "Cosmetic", "Specialized",
     "2 visits, 60–90 minutes each",
     "$900", "Cosmetic Only", True,
     "Ultra-thin porcelain shells custom-crafted to bond to the front surface of teeth, correcting discoloration, chips, gaps, or minor misalignment. Minimal tooth preparation is required. Long-lasting cosmetic enhancement with a natural translucent appearance that blends seamlessly."),
    ("Invisalign Treatment", "Orthodontic", "Specialized",
     "12–18 months total, checkups every 6–8 weeks",
     "$4,500", "Insurance Eligible, Painless", True,
     "Clear removable aligner therapy for straightening teeth without metal braces. Custom aligners are 3D-printed and changed every 1–2 weeks to gradually move teeth into position. Nearly invisible, comfortable, and removable for eating and brushing. Includes retainers upon completion."),
    ("Braces (Metal / Ceramic)", "Orthodontic", "Specialized",
     "18–24 months total, monthly adjustments",
     "$3,500", "Insurance Eligible", True,
     "Fixed orthodontic appliances using brackets and archwires to correct misalignment, overcrowding, overbites, and underbites. Metal braces are the most durable; ceramic braces offer a more discreet tooth-colored option. Monthly tightening appointments track progress over the treatment period."),
    ("Night Guard / Occlusal Splint", "Preventive", "Specialized",
     "2 visits, 20 minutes each",
     "$350", "Insurance Eligible", True,
     "A custom-fitted acrylic appliance worn during sleep to protect teeth from grinding (bruxism) and jaw clenching. Impressions are taken on the first visit and the guard is fitted on the second. Prevents enamel wear, tooth fractures, and jaw joint (TMJ) pain."),
    ("Pediatric Dental Checkup", "Preventive", "Routine",
     "30 minutes",
     "$60", "Insurance Eligible, Child-Friendly", True,
     "A comprehensive oral health examination for children aged 2–12, including visual inspection of teeth and gums, dental X-rays (if needed), and fluoride varnish application. The dentist advises on brushing technique, diet, and habits such as thumb-sucking. Scheduled every 6 months."),
    ("Fluoride Treatment", "Preventive", "Routine",
     "20 minutes",
     "$40", "Insurance Eligible, Child-Friendly", True,
     "Application of high-concentration fluoride varnish or gel directly to tooth surfaces to strengthen enamel and prevent cavities. Especially beneficial for children and patients with high cavity risk. The fluoride is left on for 4–6 hours after the appointment for maximum absorption."),
    ("Gum Disease Treatment (Gingivitis)", "Periodontic", "Routine",
     "45 minutes",
     "$120", "Insurance Eligible", True,
     "Treatment for early-stage gum disease involving professional cleaning to remove plaque and tartar from the gum line, followed by a personalized oral hygiene coaching session. With consistent home care and regular follow-up appointments, gingivitis is fully reversible."),
    ("Emergency Dental Consultation", "Emergency", "Emergency",
     "30 minutes",
     "$100", "Insurance Eligible, Same-Day Appointment", True,
     "Immediate assessment and pain relief for urgent dental issues including severe toothache, dental abscess, chipped or knocked-out teeth, and lost fillings or crowns. The dentist diagnoses the problem, provides temporary or definitive treatment, and outlines a follow-up care plan."),
    ("Dental Bridge", "Restorative", "Specialized",
     "2 visits, 60–90 minutes each",
     "$2,500", "Insurance Eligible", True,
     "A fixed prosthetic device anchored to adjacent teeth (abutments) to replace one or more missing teeth with a pontic (false tooth). Prepared teeth are fitted with crowns on either side of the gap and the bridge is permanently cemented. Restores chewing function and prevents teeth from shifting."),
    ("Dental Bonding", "Cosmetic", "Routine",
     "45 minutes",
     "$250", "Painless", True,
     "A quick, cost-effective cosmetic procedure where tooth-colored composite resin is applied and sculpted onto a tooth to repair chips, cracks, gaps, or discoloration. No anesthesia required in most cases. Results are immediate and can last 5–10 years with proper care."),
]


def get_connection():
    """Create a connection to the local SQLite database."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn):
    """Create the clinic_services table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clinic_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service_category TEXT NOT NULL,
            appointment_type TEXT NOT NULL,
            duration TEXT NOT NULL,
            price TEXT NOT NULL,
            tags TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1,
            description TEXT NOT NULL,
            description_embedding TEXT
        )
    """)
    conn.commit()


def seed_services(conn):
    """Insert clinic services."""
    cursor = conn.execute("SELECT COUNT(*) FROM clinic_services")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"      {existing_count} services already exist, skipping seed")
        return 0

    conn.executemany("""
        INSERT INTO clinic_services
            (name, service_category, appointment_type, duration, price, tags, available, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, CLINIC_SERVICES)
    conn.commit()
    return len(CLINIC_SERVICES)


def get_embedding(text):
    """Generate an embedding vector using the Google Generative AI API."""
    client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return result.embeddings[0].values


def generate_embeddings(conn):
    """Generate embeddings for services that don't have one yet."""
    cursor = conn.execute("SELECT COUNT(*) FROM clinic_services WHERE description_embedding IS NULL")
    null_count = cursor.fetchone()[0]

    if null_count == 0:
        print("      All services already have embeddings")
        return 0

    rows = conn.execute(
        "SELECT id, description FROM clinic_services WHERE description_embedding IS NULL"
    ).fetchall()

    updated = 0
    for row in rows:
        vector = get_embedding(row["description"])
        conn.execute(
            "UPDATE clinic_services SET description_embedding = ? WHERE id = ?",
            (json.dumps(vector), row["id"])
        )
        updated += 1

    conn.commit()
    return updated


def main():
    conn = get_connection()

    try:
        create_schema(conn)

        seeded = seed_services(conn)
        if seeded > 0:
            print(f"      [OK] Inserted {seeded} services")

        embedded = generate_embeddings(conn)
        if embedded > 0:
            print(f"      [OK] Generated {embedded} embeddings")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
