from datetime import datetime
from typing import Union, Dict, Any
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BPMNProcessor:
    def __init__(self, bpmn_file: str):
        self.bpmn_file = Path(bpmn_file)
        self.process_definition = self._load_bpmn()
        
    def _load_bpmn(self) -> ET.Element:
        """Load and parse the BPMN file."""
        try:
            tree = ET.parse(self.bpmn_file)
            return tree.getroot()
        except Exception as e:
            logger.error(f"Error loading BPMN file: {str(e)}")
            raise
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the BPMN process with the given input data."""
        try:
            # Start event
            logger.info("Starting BPMN process")
            
            # Validate input
            validated_data = self._validate_input(input_data)
            
            # Calculate age
            age = self._calculate_age(validated_data["date_of_birth"])
            
            # Check age condition
            is_over_21 = age >= 21
            
            # Create claim
            claim = self._create_claim(
                date_of_birth=validated_data["date_of_birth"],
                is_over_21=is_over_21
            )
            
            logger.info("BPMN process completed successfully")
            return claim
            
        except Exception as e:
            logger.error(f"Error executing BPMN process: {str(e)}")
            raise
            
    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the input data according to BPMN specification."""
        try:
            date_of_birth = input_data.get("date_of_birth")
            if not date_of_birth:
                raise ValueError("Date of birth is required")
                
            if isinstance(date_of_birth, str):
                try:
                    dob = datetime.fromisoformat(date_of_birth)
                except ValueError:
                    raise ValueError("Date of birth must be in ISO format (YYYY-MM-DD)")
            else:
                dob = date_of_birth
                
            return {
                "date_of_birth": dob
            }
        except Exception as e:
            logger.error(f"Error validating input: {str(e)}")
            raise
            
    def _calculate_age(self, date_of_birth: datetime) -> int:
        """Calculate age according to BPMN specification."""
        today = datetime.now()
        age = today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )
        return age
            
    def _create_claim(self, date_of_birth: datetime, is_over_21: bool) -> Dict[str, Any]:
        """Create age claim according to BPMN specification."""
        claim = {
            "type": "AgeVerification",
            "date_of_birth": date_of_birth.isoformat(),
            "is_over_21": is_over_21,
            "verification_date": datetime.now().isoformat(),
            "claim_id": f"age_claim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "version": "1.0"
        }
        return claim

def verify_age_claim(date_of_birth: Union[str, datetime]) -> bool:
    """Verify age claim using BPMN process."""
    try:
        processor = BPMNProcessor("templates/age_verification.bpmn")
        result = processor.execute({"date_of_birth": date_of_birth})
        return result["is_over_21"]
    except Exception as e:
        raise ValueError(f"Error processing age claim: {str(e)}")

def create_age_claim(date_of_birth: Union[str, datetime]) -> Dict[str, Any]:
    """Create age claim using BPMN process."""
    try:
        processor = BPMNProcessor("templates/age_verification.bpmn")
        return processor.execute({"date_of_birth": date_of_birth})
    except Exception as e:
        raise ValueError(f"Error creating age claim: {str(e)}")

if __name__ == "__main__":
    try:
        # Test with different dates
        test_dates = [
            "2000-01-01",  # Should be over 21
            "2003-04-27",  # Should be over 21
            "2005-01-01",  # Should be under 21
            "2002-04-27"   # Should be over 21
        ]
        
        for dob in test_dates:
            claim = create_age_claim(dob)
            print(f"\nAge Claim for DOB {dob}:")
            print(json.dumps(claim, indent=2))
            
    except Exception as e:
        print(f"Error: {str(e)}")