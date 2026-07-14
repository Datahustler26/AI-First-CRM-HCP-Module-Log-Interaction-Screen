import os
import sys

# Ensure backend folder is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from app.database import init_db, get_session, HCP, Product, Interaction
from app.agent import interact_with_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database():
    logger.info("--- Testing Database Setup ---")
    try:
        # Initialize and seed
        init_db()
        
        db = get_session()
        # Count HCPs
        hcp_count = db.query(HCP).count()
        logger.info(f"Number of seeded HCPs in database: {hcp_count}")
        assert hcp_count > 0, "No HCPs were seeded!"
        
        # Count Products
        prod_count = db.query(Product).count()
        logger.info(f"Number of seeded Products in database: {prod_count}")
        assert prod_count > 0, "No Products were seeded!"
        
        # List seeded HCPs
        hcps = db.query(HCP).all()
        for h in hcps:
            logger.info(f"  - HCP: {h.name} ({h.specialty})")
            
        db.close()
        logger.info("Database setup test passed successfully!")
    except Exception as e:
        logger.error(f"Database setup test failed: {e}")
        sys.exit(1)

def test_agent_tools():
    logger.info("\n--- Testing LangGraph Agent Tools ---")
    try:
        # Simulate chat interaction for search_hcp_history tool
        logger.info("Testing 'search_hcp_history' command...")
        res = interact_with_agent(
            message="Show me Dr. Anita Sharma's past history.",
            history=[],
            form_draft={}
        )
        logger.info(f"Agent Response:\n{res['reply']}")
        logger.info(f"Tools called: {res['tools_called']}")
        assert "search_hcp_history" in res["tools_called"], "Expected search_hcp_history tool to be called!"
        
        # Simulate chat interaction for log_interaction tool
        logger.info("\nTesting conversational 'log_interaction' command...")
        res_log = interact_with_agent(
            message="I met with Dr. Rajesh Patel today. We discussed oncology clinical trials and the sentiment was positive. Outcomes: agreed to meet next month.",
            history=[],
            form_draft={}
        )
        logger.info(f"Agent Response:\n{res_log['reply']}")
        logger.info(f"Tools called: {res_log['tools_called']}")
        logger.info(f"Updated Form Draft: {res_log['form_draft']}")
        assert "log_interaction" in res_log["tools_called"], "Expected log_interaction tool to be called!"
        
        # Verify it was saved in the db
        db = get_session()
        last_inter = db.query(Interaction).order_by(Interaction.id.desc()).first()
        logger.info(f"Verified saved interaction in DB: ID {last_inter.id}, HCP ID {last_inter.hcp_id}, Sentiment {last_inter.sentiment}")
        assert last_inter is not None, "Interaction was not saved in database!"
        db.close()
        
        logger.info("Agent tools verification completed successfully!")
    except Exception as e:
        logger.error(f"Agent tools test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_database()
    test_agent_tools()
    logger.info("\nAll tests completed successfully!")
