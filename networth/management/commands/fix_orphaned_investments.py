"""
Management command to identify and create missing transaction records for orphaned investments.
These are investments that exist but don't have associated CR (credit) transactions.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime

from networth.models import Investment, InvestmentTransaction
from networth.tools import AggregatedAsset


class Command(BaseCommand):
    help = 'Identify and create missing transaction records for orphaned investments'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Create missing transactions (default: dry run)')

    def handle(self, *args, **options):
        fix = options['fix']
        
        self.stdout.write("\n" + "█"*80)
        self.stdout.write("█ FINDING ORPHANED INVESTMENTS")
        self.stdout.write("█"*80)
        
        # Find investments with no CR (credit) transactions
        all_investments = Investment.objects.all()
        investments_with_cr = InvestmentTransaction.objects.filter(
            transaction_type='CR'
        ).values_list('investment_id', flat=True).distinct()
        
        orphaned = Investment.objects.exclude(pk__in=investments_with_cr)
        
        self.stdout.write(f"\n✓ Total investments: {all_investments.count()}")
        self.stdout.write(f"✓ Investments with CR transactions: {len(investments_with_cr)}")
        self.stdout.write(f"✓ Orphaned investments (no CR transaction): {orphaned.count()}")
        
        if not orphaned.exists():
            self.stdout.write(self.style.SUCCESS("\n✓ No orphaned investments found!"))
            return
        
        self.stdout.write(self.style.WARNING(f"\n⚠️  Found {orphaned.count()} orphaned investments:\n"))
        
        for i, investment in enumerate(orphaned, 1):
            self.stdout.write(f"{i}. Investment ID: {investment.pk}")
            self.stdout.write(f"   Owner: {investment.owner.username}")
            self.stdout.write(f"   Holder: {investment.holder}")
            self.stdout.write(f"   Principal: {investment.principal}")
            self.stdout.write(f"   Rate: {investment.rate}%")
            self.stdout.write(f"   Duration: {investment.duration} days")
            self.stdout.write(f"   Start Date: {investment.start_date}")
            self.stdout.write(f"   Host Country: {investment.host_country}")
            self.stdout.write(f"   Active: {investment.is_active}")
            self.stdout.write(f"   Existing DR transactions: {InvestmentTransaction.objects.filter(investment=investment, transaction_type='DR').count()}")
            
            # Check for DR transactions
            dr_transactions = InvestmentTransaction.objects.filter(
                investment=investment, 
                transaction_type='DR'
            )
            if dr_transactions.exists():
                self.stdout.write(f"   ⚠️  Has {dr_transactions.count()} DR transaction(s) but missing CR")
        
        if not fix:
            self.stdout.write(self.style.WARNING("\n💡 Run with --fix flag to create missing CR transactions"))
            return
        
        self.stdout.write(self.style.WARNING("\n⏳ Creating missing CR transactions...\n"))
        
        created_count = 0
        for investment in orphaned:
            try:
                # Create CR (credit) transaction for the initial investment
                description = f'Principal invested in {investment.holder} for {investment.duration} days at {investment.rate}%'
                
                transaction = InvestmentTransaction.objects.create(
                    user=investment.owner,
                    investment=investment,
                    amount=investment.principal,
                    description=description,
                    timestamp=investment.start_date,
                    transaction_type='CR'
                )
                
                self.stdout.write(self.style.SUCCESS(f"✓ Created CR transaction for Investment {investment.pk}"))
                self.stdout.write(f"  Transaction ID: {transaction.pk}")
                self.stdout.write(f"  Amount: {investment.principal}")
                self.stdout.write(f"  Timestamp: {investment.start_date}\n")
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to create transaction for Investment {investment.pk}: {e}\n"))
        
        self.stdout.write("\n" + "█"*80)
        self.stdout.write(f"█ COMPLETED: Created {created_count} missing CR transactions")
        self.stdout.write("█"*80 + "\n")
        
        # Verify the fix
        self.stdout.write("Verification:")
        orphaned_after = Investment.objects.exclude(
            pk__in=InvestmentTransaction.objects.filter(
                transaction_type='CR'
            ).values_list('investment_id', flat=True).distinct()
        )
        self.stdout.write(f"  Remaining orphaned investments: {orphaned_after.count()}")
        if orphaned_after.count() == 0:
            self.stdout.write(self.style.SUCCESS("  ✓ All investments now have CR transactions!\n"))
