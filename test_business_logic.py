#!/usr/bin/env python
"""
Comprehensive business logic verification script for networth application.
Tests Investment ROI calculations, yield percentages, and aggregations.
"""
import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nwokoro.settings')
django.setup()

from django.utils import timezone
from djmoney.money import Money
from account.models import User
from networth.models import Investment, InvestmentTransaction, ExchangeRate, FinancialData
from networth.tools import AggregatedAsset, exchange_rate


def test_investment_roi_calculations():
    """Test Investment model ROI calculation methods"""
    print("\n" + "="*80)
    print("TEST 1: Investment ROI Calculations")
    print("="*80)
    
    # Find a test user with investments
    try:
        users_with_investments = User.objects.filter(user_investments__isnull=False).distinct()
        if not users_with_investments.exists():
            print("⚠️  No users with investments found")
            return
        
        user = users_with_investments.first()
        print(f"\n✓ Testing with user: {user.username}")
        
        # Get active investments
        active_investments = Investment.objects.filter(owner=user, is_active=True)
        if not active_investments.exists():
            print("⚠️  No active investments found for this user")
            return
            
        print(f"✓ Found {active_investments.count()} active investments")
        
        # Test each investment
        for investment in active_investments[:3]:  # Test first 3
            print(f"\n  Investment: {investment.holder} ({investment.principal})")
            print(f"    Principal: {investment.principal}")
            print(f"    Rate: {investment.rate}% per annum")
            print(f"    Duration: {investment.duration} days")
            print(f"    Start Date: {investment.start_date.date()}")
            print(f"    Maturity Date: {investment.maturity()}")
            print(f"    Days Due: {investment.due_in_days()}")
            print(f"    Is Matured: {investment.is_matured()}")
            
            # Calculate ROI values
            daily_roi = investment.daily_roi()
            present_roi = investment.present_roi()
            full_roi = investment.roi()
            
            print(f"    Daily ROI: {daily_roi}")
            print(f"    Present ROI: {present_roi}")
            print(f"    Full ROI (at maturity): {full_roi}")
            
            # Verify calculations
            expected_daily = (investment.principal * Decimal(investment.rate/100)) / Decimal(365.25)
            if abs(float(daily_roi.amount) - float(expected_daily.amount)) < 0.01:
                print(f"    ✓ Daily ROI calculation verified")
            else:
                print(f"    ✗ Daily ROI calculation MISMATCH")
                print(f"      Expected: {expected_daily}, Got: {daily_roi}")
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_aggregated_asset_investments():
    """Test AggregatedAsset.investments() method"""
    print("\n" + "="*80)
    print("TEST 2: AggregatedAsset.investments() Aggregation Logic")
    print("="*80)
    
    try:
        users_with_investments = User.objects.filter(user_investments__isnull=False).distinct()
        if not users_with_investments.exists():
            print("⚠️  No users with investments found")
            return
        
        user = users_with_investments.first()
        print(f"\n✓ Testing with user: {user.username}")
        
        # Test current year aggregation
        year = timezone.now().year
        agg_current_year = AggregatedAsset(user, year)
        turnover_cy, roi_cy = agg_current_year.investments()
        
        print(f"\nCurrent Year ({year}) Aggregation:")
        print(f"  Turnover (Principal): {turnover_cy}")
        print(f"  ROI: {roi_cy}")
        if turnover_cy.amount > 0:
            yield_pct = (float(roi_cy.amount) / float(turnover_cy.amount)) * 100
            print(f"  Yield: {yield_pct:.2f}%")
            print(f"  ✓ Aggregation calculated successfully")
        else:
            print(f"  ⚠️  No investments in current year")
        
        # Test all-time aggregation
        agg_alltime = AggregatedAsset(user)
        turnover_at, roi_at = agg_alltime.investments()
        
        print(f"\nAll-Time Aggregation:")
        print(f"  Turnover (Principal): {turnover_at}")
        print(f"  ROI: {roi_at}")
        if turnover_at.amount > 0:
            yield_pct = (float(roi_at.amount) / float(turnover_at.amount)) * 100
            print(f"  Yield: {yield_pct:.2f}%")
            print(f"  ✓ Aggregation calculated successfully")
        else:
            print(f"  ⚠️  No all-time investments found")
            
        # Check if logic includes only 'DR' transactions
        dr_transactions = InvestmentTransaction.objects.filter(
            investment__owner=user, 
            transaction_type='DR'
        ).count()
        total_transactions = InvestmentTransaction.objects.filter(
            investment__owner=user
        ).count()
        
        print(f"\n⚠️  AggregatedAsset.investments() uses only 'DR' transactions:")
        print(f"    'DR' (withdrawal) transactions: {dr_transactions}")
        print(f"    Total transactions: {total_transactions}")
        print(f"    This may exclude active/immature investments without withdrawals")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_investment_score_dashboard_context():
    """Test Investment Score calculations as used in dashboard"""
    print("\n" + "="*80)
    print("TEST 3: Investment Score (Dashboard Context)")
    print("="*80)
    
    try:
        users_with_financial_data = User.objects.filter(financialdata__isnull=False).distinct()
        if not users_with_financial_data.exists():
            print("⚠️  No users with financial data found")
            return
        
        user = users_with_financial_data.first()
        print(f"\n✓ Testing with user: {user.username}")
        
        # Get latest financial data
        fd = FinancialData.objects.filter(owner=user).latest('date')
        print(f"✓ Financial data date: {fd.date}")
        
        # Replicate dashboard Investment Score logic
        year = timezone.now().year
        
        # Current year
        current_year_asset = AggregatedAsset(user, year)
        ytd_turnover, ytd_roi_val = current_year_asset.investments()
        
        ytd_yield_pct = (
            round(float(ytd_roi_val.amount) / float(ytd_turnover.amount) * 100, 1)
            if ytd_turnover.amount else 0
        )
        
        print(f"\nCurrent Year ({year}):")
        print(f"  Turnover: {ytd_turnover}")
        print(f"  ROI Earned: {ytd_roi_val}")
        print(f"  Yield: {ytd_yield_pct}%")
        
        # All-time
        alltime_asset = AggregatedAsset(user)
        alltime_turnover, alltime_roi = alltime_asset.investments()
        
        alltime_yield_pct = (
            round(float(alltime_roi.amount) / float(alltime_turnover.amount) * 100, 1)
            if alltime_turnover.amount else 0
        )
        
        print(f"\nAll-Time:")
        print(f"  Turnover: {alltime_turnover}")
        print(f"  ROI Earned: {alltime_roi}")
        print(f"  Yield: {alltime_yield_pct}%")
        
        # Check unrealized earnings
        if fd.present_roi:
            total_roi_at_maturity = fd.roi
            if total_roi_at_maturity.amount > 0:
                present_roi_pct = (
                    round(float(fd.present_roi.amount) / float(total_roi_at_maturity.amount) * 100, 1)
                )
                print(f"\nUnrealized Earnings:")
                print(f"  Present ROI: {fd.present_roi}")
                print(f"  Total ROI at Maturity: {total_roi_at_maturity}")
                print(f"  Completion %: {present_roi_pct}%")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_exchange_rate_conversions():
    """Test exchange rate conversions in ROI calculations"""
    print("\n" + "="*80)
    print("TEST 4: Exchange Rate Conversions")
    print("="*80)
    
    try:
        # Check available exchange rates
        rates = ExchangeRate.objects.all()
        if not rates.exists():
            print("⚠️  No exchange rates found in database")
            return
        
        print(f"✓ Found {rates.count()} exchange rates:")
        for rate in rates:
            print(f"  {rate.base_currency} -> {rate.target_currency}: {rate.rate}")
        
        # Test exchange_rate helper function
        print(f"\nTesting exchange_rate() helper function:")
        for currency in ['NGN', 'CAD', 'USD']:
            result = exchange_rate(currency)
            if result:
                rate_money, updated_at = result
                print(f"  {currency}: {rate_money} (updated {updated_at})")
            else:
                print(f"  {currency}: No rate found")
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def test_data_integrity():
    """Test overall data integrity and consistency"""
    print("\n" + "="*80)
    print("TEST 5: Data Integrity Checks")
    print("="*80)
    
    try:
        # Check for orphaned transactions
        orphaned_inv_txns = InvestmentTransaction.objects.filter(investment__isnull=True)
        if orphaned_inv_txns.exists():
            print(f"✗ Found {orphaned_inv_txns.count()} orphaned investment transactions")
        else:
            print(f"✓ No orphaned investment transactions")
        
        # Check for investments with no transactions
        investments_no_txn = Investment.objects.exclude(
            pk__in=InvestmentTransaction.objects.values_list('investment_id', flat=True).distinct()
        )
        if investments_no_txn.exists():
            print(f"⚠️  Found {investments_no_txn.count()} investments with no transactions")
            print("   These investments won't appear in Investment Score calculations")
        else:
            print(f"✓ All investments have associated transactions")
        
        # Check financial data consistency
        print(f"\nFinancial Data Records:")
        fd_count = FinancialData.objects.count()
        print(f"  Total records: {fd_count}")
        if fd_count > 0:
            latest_fd = FinancialData.objects.latest('date')
            print(f"  Latest date: {latest_fd.date}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "█"*80)
    print("█ NETWORTH APPLICATION - BUSINESS LOGIC VERIFICATION")
    print("█"*80)
    
    test_investment_roi_calculations()
    test_aggregated_asset_investments()
    test_investment_score_dashboard_context()
    test_exchange_rate_conversions()
    test_data_integrity()
    
    print("\n" + "█"*80)
    print("█ VERIFICATION COMPLETE")
    print("█"*80 + "\n")
