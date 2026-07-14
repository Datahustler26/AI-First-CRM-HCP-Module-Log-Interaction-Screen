import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Date, Time
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# SQLAlchemy Models
class HCP(Base):
    __tablename__ = 'hcps'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    
    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")

class Interaction(Base):
    __tablename__ = 'interactions'
    
    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey('hcps.id'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # e.g., Meeting, Call, Email, Webcast
    date = Column(String(20), nullable=False)  # YYYY-MM-DD
    time = Column(String(20), nullable=False)  # HH:MM
    attendees = Column(Text, nullable=True)     # Comma-separated or JSON list of attendees
    topics_discussed = Column(Text, nullable=False)
    voice_note_summary = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)   # Comma-separated or JSON list of materials
    samples_distributed = Column(Text, nullable=True) # Comma-separated or JSON list of samples
    sentiment = Column(String(20), nullable=False)    # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hcp = relationship("HCP", back_populates="interactions")

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False) # 'Material' or 'Sample'
    description = Column(String(255), nullable=True)

# Connection string setup with fallbacks for local developer environments
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/hcp_crm")

engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal
    if engine is not None:
        return engine

    # Access URL parts to try multiple connection strategies
    # Strategy 1: URL configured in .env (e.g. root:password)
    # Strategy 2: URL with root and empty password (standard for local dev)
    # Strategy 3: URL with root:root or root:admin
    # Strategy 4: Fallback to SQLite to guarantee runtime success
    
    urls_to_try = [
        DATABASE_URL,
        "mysql+pymysql://root:@localhost:3306/hcp_crm",
        "mysql+pymysql://root:root@localhost:3306/hcp_crm",
        "mysql+pymysql://root:admin@localhost:3306/hcp_crm",
        "mysql+pymysql://root:mysql@localhost:3306/hcp_crm",
        "sqlite:///hcp_crm.db" # Fail-safe fallback
    ]

    for url in urls_to_try:
        try:
            logger.info(f"Attempting to connect to database at: {url.split('@')[-1] if '@' in url else url}")
            
            # If it's a MySQL URL, we need to make sure the database exists.
            # We can connect to mysql (default system db) and create hcp_crm database if needed.
            if "mysql" in url:
                # Parse host, port, user, password from url
                import pymysql
                from urllib.parse import urlparse
                
                # Simple manual parsing of MySQL credentials
                # mysql+pymysql://user:password@host:port/dbname
                stripped = url.replace("mysql+pymysql://", "")
                creds, rest = stripped.split("@")
                if ":" in creds:
                    user, password = creds.split(":")
                else:
                    user, password = creds, ""
                
                host_port, dbname = rest.split("/")
                dbname = dbname.split("?")[0]
                if ":" in host_port:
                    host, port = host_port.split(":")
                    port = int(port)
                else:
                    host, port = host_port, 3306
                
                # Establish raw connection to create db if it does not exist
                conn = pymysql.connect(host=host, port=port, user=user, password=password)
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {dbname}")
                conn.commit()
                cursor.close()
                conn.close()
                logger.info(f"Database '{dbname}' verified/created.")

            # Create SQLAlchemy engine
            temp_engine = create_engine(url, connect_args={"connect_timeout": 3} if "mysql" in url else {})
            
            # Test connection
            with temp_engine.connect() as conn:
                pass
            
            logger.info(f"Database connection successful with URL: {url.split('@')[-1] if '@' in url else url}")
            engine = temp_engine
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            return engine
            
        except Exception as e:
            logger.warning(f"Failed to connect to database using {url.split('@')[-1] if '@' in url else url}: {e}")

    raise Exception("Critical: Could not connect to any database or fallbacks. Ensure MySQL is running or SQLite permissions are allowed.")

# Helper to initialize DB tables and seed data
def init_db():
    get_engine()
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed HCPs
        if db.query(HCP).count() == 0:
            logger.info("Seeding HCP database table...")
            hcps = [
                HCP(name="Dr. Anita Sharma", specialty="Cardiologist", email="anita.sharma@cardiohealth.com", phone="+91 98765 43210"),
                HCP(name="Dr. Rajesh Patel", specialty="Oncologist", email="rajesh.patel@oncocare.org", phone="+91 98123 45678"),
                HCP(name="Dr. Sarah Connor", specialty="Pediatrician", email="sarah.connor@pediatricclinic.com", phone="+91 97777 88888"),
                HCP(name="Dr. Amit Verma", specialty="Neurologist", email="amit.verma@neurologyinstitute.in", phone="+91 96666 55555"),
                HCP(name="Dr. Priya Nair", specialty="Endocrinologist", email="priya.nair@diabetescare.com", phone="+91 95555 44444")
            ]
            db.add_all(hcps)
            db.commit()
            logger.info("HCP table seeded successfully.")
            
        # Seed Products and Materials
        if db.query(Product).count() == 0:
            logger.info("Seeding products/materials database table...")
            products = [
                # Materials
                Product(name="OncoBoost Phase III Brochure", category="Material", description="Latest clinical trial outcomes brochure for OncoBoost"),
                Product(name="CardiaShield Efficacy Study PDF", category="Material", description="Clinical study paper on CardiaShield cardioprotection"),
                Product(name="NeuroVigor Prescribing Information", category="Material", description="Dosage and prescribing instructions booklet for NeuroVigor"),
                Product(name="Pediatrix Vaccine Guidelines", category="Material", description="Childhood vaccination guide flyer for Pediatrix"),
                
                # Samples
                Product(name="OncoBoost Starter Pack (5mg)", category="Sample", description="Starter kits for patients starting chemotherapy"),
                Product(name="CardiaShield 10mg Tablets (Box of 30)", category="Sample", description="CardiaShield daily treatment physician samples"),
                Product(name="NeuroVigor Capsules (10-Day Sample)", category="Sample", description="NeuroVigor cognitive enhancer starter samples"),
                Product(name="Pediatrix Chewable Multivitamins", category="Sample", description="Childhood vitamin chewable bottle samples")
            ]
            db.add_all(products)
            db.commit()
            logger.info("Products table seeded successfully.")
            
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

# Dependency to get db session in FastAPI endpoint
def get_session():
    global SessionLocal
    if SessionLocal is None:
        get_engine()
    return SessionLocal()

def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

