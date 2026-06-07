"""
Comprehensive business logic verification command for networth application.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from djmoney.money import Money
from decimal import Decimal

from account.models import User
from networth.models import Investment, InvestmentTransaction, ExchangeRate, FinancialData
from networth.tools import AggregatedAsset, exchange_rate


class Command(BaseCommand):
    help = 'Verify business logic correctness'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username to test')

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("= NETWORTH APPLICATION - BUSINESS LOGIC VERIFICATION")
        self.stdout.write("="*80)
        
        self.test_investment_roi_calculations()
        self.test_aggregated_asset_investments()
        self.test_investment_score_dashboard_context()
        self.test_exchange_rate_conversions()
        self.test_data_integrity()
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("= VERIFICATION COMPLETE")
        self.stdout.write("="*80 + "\n")

    def test_investment_roi_calculations(self):
        """Test Investment model ROI calculation methods"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TEST 1: Investment ROI Calculations")
        self.stdout.write("="*80)
        
        try:
            users_with_investments = User.objects.filter(user_investments__isnull=False).distinct()
            if not users_with_investments.exists():
                self.stdout.write(self.style.WARNING("⚠️  No users with investments found"))
                return
            
            user = users_with_investments.first()
            self.stdout.write(f"\n✓ Testing with user: {user.username}")
            
            active_investments = Investment.objects.filter(owner=user, is_active=True)
            if not active_investments.exists():
                self.stdout.write(self.style.WARNING("⚠️  No active investments found"))
                return
                
            self.stdout.write(f"✓ Found {active_investments.count()} active investments")
            
            for investment in active_investments[:3]:
                self.stdout.write(f"\n  Investment: {investment.holder} ({investment.principal})")
                self.stdout.write(f"    Principal: {investment.principal}")
                self.stdout.write(f"    Rate: {investment.rate}% per annum")
                self.stdout.write(f"    Duration: {investment.duration} days")
                self.stdout.write(f"    Start Date: {investment.start_date.date()}")
                self.stdout.write(f"    Maturity Date: {investment.maturity()}")
                self.stdout.write(f"    Days Due: {investment.due_in_days()}")
                self.stdout.write(f"    Is Matured: {investment.is_matured()}")
                
                daily_roi = investment.daily_roi()
                present_roi = investment.present_roi()
                full_roi = investment.roi()
                
                self.stdout.write(f"    Daily ROI: {daily_roi}")
                self.stdout.write(f"    Present ROI: {present_roi}")
                self.stdout.write(f"    Full ROI (at maturity): {full_roi}")
                
                expected_daily = (investment.principal * Decimal(investment.rate/100)) / Decimal(365.25)
                if abs(float(daily_roi.amount) - float(expected_daily.amount)) < 0.01:
                    self.stdout.write(self.style.SUCCESS("    ✓ Daily ROI calculation verified"))
                else:
                    self.stdout.write(self.style.ERROR(f"    ✗ Daily ROI calculation MISMATCH"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
            import traceback
            traceback.print_exc()

    def test_aggregated_asset_investments(self):
        """Test AggregatedAsset.investments() method"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TEST 2: AggregatedAsset.investments() Aggregation Logic")
        self.stdout.write("="*80)
        
        try:
            users_with_investments = User.objects.filter(user_investments__isnull=False).distinct()
            if not users_with_investments.exists():
                self.stdout.write(self.style.WARNING("⚠️  No users with investments found"))
                return
            
            user = users_with_investments.first()
            self.stdout.write(f"\n✓ Testing with user: {user.username}")
            
            year = timezone.now().year
            agg_current_year = AggregatedAsset(user, year)
            turnover_cy, roi_cy = agg_current_year.investments()
            
            self.stdout.write(f"\nCurrent Year ({year}) Aggregation:")
            self.stdout.write(f"  Turnover (Principal): {turnover_cy}")
            self.stdout.write(f"  ROI: {roi_cy}")
            if turnover_cy.amount > 0:
                yield_pct = (float(roi_cy.amount) / float(turnover_cy.amount)) * 100
                self.stdout.write(f"  Yield: {yield_pct:.2f}%")
                self.stdout.write(self.style.SUCCESS("  ✓ Aggregation calculated successfully"))
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  No investments in current year"))
            
            agg_alltime = AggregatedAsset(user)
            turnover_at, roi_at = agg_alltime.investments()
            
            self.stdout.write(f"\nAll-Time Aggregation:")
            self.stdout.write(f"  Turnover (Principal): {turnover_at}")
            self.stdout.write(f"  ROI: {roi_at}")
            if turnover_at.amount > 0:
                yield_pct = (float(roi_at.amount) / float(turnover_at.amount)) * 100
                self.stdout.write(f"  Yield: {yield_pct:.2f}%")
                self.stdout.write(self.style.SUCCESS("  ✓ Aggregation calculated successfully"))
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  No all-time investments found"))
            
            dr_transactions = InvestmentTransaction.objects.filter(
                investment__owner=user, 
                transaction_type='DR'
            ).count()
            total_transactions = InvestmentTransaction.objects.filter(
                investment__owner=user
            ).count()
            
            self.stdout.write(self.style.WARNING(f"\n⚠️  AggregatedAsset.investments() uses only 'DR' transactions:"))
            self.stdout.write(f"    'DR' (withdrawal) transactions: {dr_transactions}")
            self.stdout.write(f"    Total transactions: {total_transactions}")
            self.stdout.write(f"    This may exclude active/immature investments without withdrawals")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
            import traceback
            traceback.print_exc()

    def test_investment_score_dashboard_context(self):
        """Test Investment Score calculations as used in dashboard"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TEST 3: Investment Score (Dashboard Context)")
        self.stdout.write("="*80)
        
        try:
            users_with_fd = User.objects.filter(financialdata__isnull=False).distinct()
            if not users_with_fd.exists():
                self.stdout.write(self.style.WARNING("⚠️  No users with financial data found"))
                return
            
            user = users_with_fd.first()
            self.stdout.write(f"\n✓ Testing with user: {user.username}")
            
            fd = FinancialData.objects.filter(owner=user).latest('date')
            self.stdout.write(f"✓ Financial data date: {fd.date}")
            
            year = timezone.now().year
            
            current_year_asset = AggregatedAsset(user, year)
            ytd_turnover, ytd_roi_val = current_year_asset.investments()
            
            ytd_yield_pct = (
                round(float(ytd_roi_val.amount) / float(ytd_turnover.amount) * 100, 1)
                if ytd_turnover.amount else 0
            )
            
            self.stdout.write(f"\nCurrent Year ({year}):")
            self.stdout.write(f"  Turnover: {ytd_turnover}")
            self.stdout.write(f"  ROI Earned: {ytd_roi_val}")
            self.stdout.write(f"  Yield: {ytd_yield_pct}%")
            
            alltime_asset = AggregatedAsset(user)
            alltime_turnover, alltime_roi = alltime_asset.investments()
            
            alltime_yield_pct = (
                round(float(alltime_roi.amount) / float(alltime_turnover.amount) * 100, 1)
                if alltime_turnover.amount else 0
            )
            
            self.stdout.write(f"\nAll-Time:")
            self.stdout.write(f"  Turnover: {alltime_turnover}")
            self.stdout.write(f"  ROI Earned: {alltime_roi}")
            self.stdout.write(f"  Yield: {alltime_yield_pct}%")
            
            if fd.present_roi:
                total_roi_at_maturity = fd.roi
                if total_roi_at_maturity.amount > 0:
                    present_roi_pct = (
                        round(float(fd.present_roi.amount) / float(total_roi_at_maturity.amount) * 100, 1)
                    )
                    self.stdout.write(f"\nUnrealized Earnings:")
                    self.stdout.write(f"  Present ROI: {fd.present_roi}")
                    self.stdout.write(f"  Total ROI at Maturity: {total_roi_at_maturity}")
                    self.stdout.write(f"  Completion %: {present_roi_pct}%")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
            import traceback
            traceback.print_exc()

    def test_exchange_rate_conversions(self):
        """Test exchange rate conversions in ROI calculations"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TEST 4: Exchange Rate Conversions")
        self.stdout.write("="*80)
        
        try:
            rates = ExchangeRate.objects.all()
            if not rates.exists():
                self.stdout.write(self.style.WARNING("⚠️  No exchange rates found"))
                return
            
            self.stdout.write(f"✓ Found {rates.count()} exchange rates:")
            for rate in rates:
                self.stdout.write(f"  {rate.base_currency} -> {rate.target_currency}: {rate.rate}")
            
            self.stdout.write(f"\nTesting exchange_rate() helper function:")
            for currency in ['NGN', 'CAD', 'USD']:
                result = exchange_rate(currency)
                if result:
                    rate_money, updated_at = result
                    self.stdout.write(f"  {currency}: {rate_money} (updated {updated_at})")
                else:
                    self.stdout.write(self.style.WARNING(f"  {currency}: No rate found"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))

    def test_data_integrity(self):
        """Test overall data integrity and consistency"""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TEST 5: Data Integrity Checks")
        self.stdout.write("="*80)
        
        try:
            orphaned_inv_txns = InvestmentTransaction.objects.filter(investment__isnull=True)
            if orphaned_inv_txns.exists():
                self.stdout.write(self.style.ERROR(f"✗ Found {orphaned_inv_txns.count()} orphaned transactions"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ No orphaned investment transactions"))
            
            investments_no_txn = Investment.objects.exclude(
                pk__in=InvestmentTransaction.objects.values_list('investment_id', flat=True).distinct()
            )
            if investments_no_txn.exists():
                self.stdout.write(self.style.WARNING(f"⚠️  Found {investments_no_txn.count()} investments with no transactions"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ All investments have associated transactions"))
            
            self.stdout.write(f"\nFinancial Data Records:")
            fd_count = FinancialData.objects.count()
            self.stdout.write(f"  Total records: {fd_count}")
            if fd_count > 0:
                latest_fd = FinancialData.objects.latest('date')
                self.stdout.write(f"  Latest date: {latest_fd.date}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {e}"))
