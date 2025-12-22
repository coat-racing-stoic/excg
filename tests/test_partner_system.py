"""
Tests for partner_system.py - Partner commission calculation module
"""
import pytest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partner_system import PartnerSystem, partner_system
from models import PartnerCalculation


class TestPartnerSystem:
    """Tests for PartnerSystem class"""
    
    @pytest.fixture
    def system(self):
        """Create fresh PartnerSystem instance"""
        return PartnerSystem()
    
    def test_init(self, system):
        """Test PartnerSystem initialization"""
        assert system.partners == {}
    
    def test_add_partner(self, system):
        """Test adding a partner"""
        system.add_partner("TEST001", 1.0, 5.0)
        
        assert "TEST001" in system.partners
        assert system.partners["TEST001"]["default_commission"] == 1.0
        assert system.partners["TEST001"]["max_commission"] == 5.0
    
    def test_add_multiple_partners(self, system):
        """Test adding multiple partners"""
        system.add_partner("PARTNER1", 1.0, 5.0)
        system.add_partner("PARTNER2", 2.0, 10.0)
        system.add_partner("PARTNER3", 3.0, 15.0)
        
        assert len(system.partners) == 3
        assert "PARTNER1" in system.partners
        assert "PARTNER2" in system.partners
        assert "PARTNER3" in system.partners
    
    def test_get_partner_info_existing(self, system):
        """Test getting info for existing partner"""
        system.add_partner("TEST001", 1.5, 7.5)
        
        info = system.get_partner_info("TEST001")
        
        assert info is not None
        assert info["default_commission"] == 1.5
        assert info["max_commission"] == 7.5
    
    def test_get_partner_info_nonexistent(self, system):
        """Test getting info for non-existent partner"""
        info = system.get_partner_info("NONEXISTENT")
        
        assert info is None


class TestPartnerValidation:
    """Tests for partner request validation"""
    
    @pytest.fixture
    def system(self):
        """Create fresh PartnerSystem instance"""
        return PartnerSystem()
    
    def test_validate_no_params(self, system):
        """Test validation with no partner parameters"""
        result = system.validate_partner_request(None, None)
        
        assert result is True
    
    def test_validate_both_params(self, system):
        """Test validation with both parameters"""
        result = system.validate_partner_request("TEST001", 2.5)
        
        assert result is True
    
    def test_validate_refcode_only(self, system):
        """Test validation with refcode only (should fail)"""
        result = system.validate_partner_request("TEST001", None)
        
        assert result is False
    
    def test_validate_afftax_only(self, system):
        """Test validation with afftax only (should fail)"""
        result = system.validate_partner_request(None, 2.5)
        
        assert result is False
    
    def test_validate_negative_afftax(self, system):
        """Test validation with negative afftax"""
        result = system.validate_partner_request("TEST001", -1.0)
        
        assert result is False
    
    def test_validate_afftax_over_100(self, system):
        """Test validation with afftax over 100%"""
        result = system.validate_partner_request("TEST001", 101.0)
        
        assert result is False
    
    def test_validate_afftax_zero(self, system):
        """Test validation with zero afftax - zero is falsy so treated as no afftax"""
        result = system.validate_partner_request("TEST001", 0.0)
        
        # Zero afftax is falsy, so it's treated as "no afftax" which fails validation
        # when refcode is provided (refcode without afftax is invalid)
        assert result is False
    
    def test_validate_afftax_100(self, system):
        """Test validation with 100% afftax"""
        result = system.validate_partner_request("TEST001", 100.0)
        
        assert result is True


class TestCommissionCalculation:
    """Tests for commission calculation formulas"""
    
    @pytest.fixture
    def system(self):
        """Create fresh PartnerSystem instance"""
        ps = PartnerSystem()
        ps.add_partner("TEST001", 1.0, 5.0)
        return ps
    
    def test_calculate_no_params(self, system):
        """Test calculation with no partner parameters"""
        result = system.calculate_commission(None, None, 2.0, 0.5)
        
        assert isinstance(result, PartnerCalculation)
        assert result.total_commission == 0.0
        assert "No partner code" in result.formula_used
    
    def test_calculate_no_refcode(self, system):
        """Test calculation with no refcode"""
        result = system.calculate_commission(None, 2.5, 2.0, 0.5)
        
        assert result.total_commission == 0.0
    
    def test_calculate_no_afftax(self, system):
        """Test calculation with no afftax"""
        result = system.calculate_commission("TEST001", None, 2.0, 0.5)
        
        assert result.total_commission == 0.0
    
    def test_formula_1_afftax_less_than_ff_minus_affb(self, system):
        """Test Formula 1: afftax < (FF - AFFB)
        
        When afftax < (FF - AFFB):
        total = FF - AFFB + afftax
        
        Example: FF=2.0, AFFB=0.5, afftax=1.0
        FF - AFFB = 1.5
        afftax (1.0) < 1.5, so use Formula 1
        total = 2.0 - 0.5 + 1.0 = 2.5
        """
        ff = 2.0
        affb = 0.5
        afftax = 1.0  # Less than FF - AFFB (1.5)
        
        result = system.calculate_commission("TEST001", afftax, ff, affb)
        
        expected_total = ff - affb + afftax  # 2.0 - 0.5 + 1.0 = 2.5
        assert result.total_commission == expected_total
        assert "FF" in result.formula_used and "AFFB" in result.formula_used
    
    def test_formula_2_afftax_between_ff_minus_affb_and_ff(self, system):
        """Test Formula 2: (FF - AFFB) <= afftax < FF
        
        When (FF - AFFB) <= afftax < FF:
        total = afftax × 2
        
        Example: FF=2.0, AFFB=0.5, afftax=1.8
        FF - AFFB = 1.5
        1.5 <= afftax (1.8) < 2.0, so use Formula 2
        total = 1.8 × 2 = 3.6
        """
        ff = 2.0
        affb = 0.5
        afftax = 1.8  # Between FF - AFFB (1.5) and FF (2.0)
        
        result = system.calculate_commission("TEST001", afftax, ff, affb)
        
        expected_total = afftax * 2  # 1.8 × 2 = 3.6
        assert result.total_commission == expected_total
        assert "× 2" in result.formula_used
    
    def test_formula_2_afftax_equals_ff_minus_affb(self, system):
        """Test Formula 2 boundary: afftax == (FF - AFFB)"""
        ff = 2.0
        affb = 0.5
        afftax = 1.5  # Exactly FF - AFFB
        
        result = system.calculate_commission("TEST001", afftax, ff, affb)
        
        expected_total = afftax * 2  # 1.5 × 2 = 3.0
        assert result.total_commission == expected_total
    
    def test_formula_3_afftax_greater_than_ff(self, system):
        """Test Formula 3: afftax > FF
        
        When afftax > FF:
        total = FF + afftax
        
        Example: FF=2.0, AFFB=0.5, afftax=3.0
        afftax (3.0) > FF (2.0), so use Formula 3
        total = 2.0 + 3.0 = 5.0
        """
        ff = 2.0
        affb = 0.5
        afftax = 3.0  # Greater than FF
        
        result = system.calculate_commission("TEST001", afftax, ff, affb)
        
        expected_total = ff + afftax  # 2.0 + 3.0 = 5.0
        assert result.total_commission == expected_total
        assert "FF" in result.formula_used and "afftax" in result.formula_used
    
    def test_formula_3_afftax_equals_ff(self, system):
        """Test Formula 3 boundary: afftax == FF"""
        ff = 2.0
        affb = 0.5
        afftax = 2.0  # Exactly FF
        
        result = system.calculate_commission("TEST001", afftax, ff, affb)
        
        # When afftax == FF, it's >= FF, so Formula 3 applies
        expected_total = ff + afftax  # 2.0 + 2.0 = 4.0
        assert result.total_commission == expected_total
    
    def test_calculation_returns_partner_calculation_model(self, system):
        """Test that calculation returns PartnerCalculation model"""
        result = system.calculate_commission("TEST001", 1.5, 2.0, 0.5)
        
        assert isinstance(result, PartnerCalculation)
        assert result.refcode == "TEST001"
        assert result.afftax == 1.5
        assert isinstance(result.total_commission, float)
        assert isinstance(result.formula_used, str)


class TestGlobalPartnerSystem:
    """Tests for global partner_system instance"""
    
    def test_global_instance_exists(self):
        """Test that global partner_system instance exists"""
        assert partner_system is not None
        assert isinstance(partner_system, PartnerSystem)
    
    def test_demo_partners_loaded(self):
        """Test that demo partners are loaded"""
        # Check demo partners from partner_system.py
        assert "DEMO001" in partner_system.partners
        assert "DEMO002" in partner_system.partners
        assert "PREMIUM" in partner_system.partners
    
    def test_demo001_config(self):
        """Test DEMO001 partner configuration"""
        info = partner_system.get_partner_info("DEMO001")
        
        assert info is not None
        assert info["default_commission"] == 1.0
        assert info["max_commission"] == 5.0
    
    def test_demo002_config(self):
        """Test DEMO002 partner configuration"""
        info = partner_system.get_partner_info("DEMO002")
        
        assert info is not None
        assert info["default_commission"] == 2.0
        assert info["max_commission"] == 10.0
    
    def test_premium_config(self):
        """Test PREMIUM partner configuration"""
        info = partner_system.get_partner_info("PREMIUM")
        
        assert info is not None
        assert info["default_commission"] == 5.0
        assert info["max_commission"] == 15.0


class TestEdgeCases:
    """Edge case tests for partner system"""
    
    @pytest.fixture
    def system(self):
        """Create fresh PartnerSystem instance"""
        return PartnerSystem()
    
    def test_zero_ff_and_affb(self, system):
        """Test calculation with zero FF and AFFB"""
        result = system.calculate_commission("TEST", 1.0, 0.0, 0.0)
        
        # afftax (1.0) > FF (0.0), so Formula 3: total = FF + afftax = 0 + 1 = 1
        assert result.total_commission == 1.0
    
    def test_large_values(self, system):
        """Test calculation with large values"""
        result = system.calculate_commission("TEST", 50.0, 100.0, 10.0)
        
        # FF - AFFB = 90, afftax (50) < 90, so Formula 1
        # total = 100 - 10 + 50 = 140
        assert result.total_commission == 140.0
    
    def test_small_decimal_values(self, system):
        """Test calculation with small decimal values"""
        result = system.calculate_commission("TEST", 0.001, 0.01, 0.005)
        
        # FF - AFFB = 0.005, afftax (0.001) < 0.005, so Formula 1
        # total = 0.01 - 0.005 + 0.001 = 0.006
        assert abs(result.total_commission - 0.006) < 0.0001
    
    def test_empty_refcode(self, system):
        """Test calculation with empty refcode"""
        result = system.calculate_commission("", 1.0, 2.0, 0.5)
        
        # Empty string is falsy, so should return 0
        assert result.total_commission == 0.0
    
    def test_zero_afftax(self, system):
        """Test calculation with zero afftax"""
        result = system.calculate_commission("TEST", 0.0, 2.0, 0.5)
        
        # Zero is falsy, so should return 0
        assert result.total_commission == 0.0
