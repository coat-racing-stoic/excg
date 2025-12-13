from typing import Optional, Dict, Any
from models import PartnerCalculation

class PartnerSystem:
    """Partner commission calculation system"""
    
    def __init__(self):
        # In production, load partner data from database
        self.partners: Dict[str, Dict[str, Any]] = {}
    
    def add_partner(self, refcode: str, default_commission: float, max_commission: float):
        """Add a partner with their commission settings"""
        self.partners[refcode] = {
            "default_commission": default_commission,
            "max_commission": max_commission
        }
    
    def calculate_commission(self, refcode: Optional[str], afftax: Optional[float], 
                           ff: float, affb: float) -> PartnerCalculation:
        """
        Calculate partner commission based on FixedFloat formula
        
        Args:
            refcode: Partner referral code
            afftax: Desired commission percentage
            ff: FixedFloat fee
            affb: Affiliate base commission
            
        Returns:
            PartnerCalculation with calculated commission and formula used
        """
        if not refcode or not afftax:
            return PartnerCalculation(
                refcode=refcode or "",
                afftax=afftax or 0.0,
                total_commission=0.0,
                formula_used="No partner code or commission specified"
            )
        
        # Validate partner exists (in production, check database)
        if refcode not in self.partners:
            # For demo purposes, allow any refcode
            pass
        
        # Apply FixedFloat commission calculation formula
        if afftax < (ff - affb):
            # Formula 1: total = FF - AFFB + afftax
            total = ff - affb + afftax
            formula = f"FF({ff}) - AFFB({affb}) + afftax({afftax}) = {total}"
        elif (ff - affb) <= afftax < ff:
            # Formula 2: total = afftax × 2
            total = afftax * 2
            formula = f"afftax({afftax}) × 2 = {total}"
        else:
            # Formula 3: total = FF + afftax
            total = ff + afftax
            formula = f"FF({ff}) + afftax({afftax}) = {total}"
        
        return PartnerCalculation(
            refcode=refcode,
            afftax=afftax,
            total_commission=total,
            formula_used=formula
        )
    
    def validate_partner_request(self, refcode: Optional[str], afftax: Optional[float]) -> bool:
        """Validate partner request parameters"""
        if not refcode and not afftax:
            return True  # No partner parameters provided
        
        if refcode and not afftax:
            return False  # Partner code without commission
        
        if afftax and not refcode:
            return False  # Commission without partner code
        
        if afftax and (afftax < 0 or afftax > 100):
            return False  # Invalid commission percentage
        
        return True
    
    def get_partner_info(self, refcode: str) -> Optional[Dict[str, Any]]:
        """Get partner information"""
        return self.partners.get(refcode)

# Global partner system instance
partner_system = PartnerSystem()

# Add some demo partners
partner_system.add_partner("DEMO001", 1.0, 5.0)
partner_system.add_partner("DEMO002", 2.0, 10.0)
partner_system.add_partner("PREMIUM", 5.0, 15.0)