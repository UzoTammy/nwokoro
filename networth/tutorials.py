"""
Static content for the "Learn" investment tutorial section. Kept as plain
Python data (no model/migration) since it's editorial content, not user data.
"""

INVESTMENT_TUTORIALS = [
    {
        'slug': 'stocks',
        'title': 'Stocks (Equities)',
        'icon': 'fa-chart-line',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Buying a share of ownership in a public company, betting on its future earnings and growth.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-building', 'label': 'Public Company'},
            {'icon': 'fa-hand-holding-usd', 'label': 'Dividends & Price Growth'},
        ],
        'content': [
            "A stock represents a slice of ownership in a company. When you buy shares, you become a "
            "part-owner and your return comes from two places: price appreciation (the share becoming "
            "worth more) and dividends (a portion of profit paid out to shareholders).",
            "Stocks are traded on public exchanges, so prices move constantly based on company "
            "performance, interest rates, and overall market sentiment. That liquidity is a strength — "
            "you can usually buy or sell within seconds — but it also means short-term prices can swing "
            "sharply even when nothing about the underlying business has changed.",
            "Over long time horizons, equities have historically outpaced inflation and most other asset "
            "classes, which is why they're a core holding in most portfolios. The tradeoff is volatility: "
            "a stock can lose a large share of its value in a downturn, and there's no guarantee it "
            "recovers on any particular timeline.",
        ],
        'key_points': [
            "Ownership stake — returns come from price growth and dividends.",
            "Highly liquid: easy to buy and sell on public exchanges.",
            "Volatile in the short term; historically strong over long horizons.",
            "Diversifying across many companies/sectors reduces single-company risk.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Stocks',
            'scenario': [
                "Say you invest $200 a month into a diversified stock index fund starting at age 25. "
                "Assuming a historical long-run average return of around 7% after inflation, that steady "
                "monthly habit alone could grow to roughly $480,000 by age 65 — not from any single stock "
                "picked well, but from time in the market and consistent contributions.",
                "The engine behind this is compounding: each year's gains start earning their own gains. "
                "Reinvesting dividends rather than spending them accelerates this further, since those "
                "payouts buy more shares that then also grow.",
            ],
            'strategies': [
                "Automate regular contributions (dollar-cost averaging) so you buy through both dips and "
                "highs without trying to time the market.",
                "Reinvest dividends automatically rather than withdrawing them, so gains compound instead "
                "of sitting idle.",
                "Diversify across many companies and sectors (e.g. via an index fund) instead of "
                "concentrating in a few stocks.",
                "Give it time — the biggest driver of stock growth for most investors is years invested, "
                "not clever trading.",
            ],
            'caution': "Past returns don't guarantee future ones, and stock values can fall sharply in any "
                       "given year — this works best as a long-term strategy, not a short-term bet.",
        },
    },
    {
        'slug': 'bonds',
        'title': 'Bonds (Fixed Income)',
        'icon': 'fa-file-invoice-dollar',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'Lending money to a government or company in exchange for regular interest payments.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-landmark', 'label': 'Government / Corporation'},
            {'icon': 'fa-coins', 'label': 'Interest + Principal'},
        ],
        'content': [
            "A bond is essentially a loan. You give an issuer — a government or a corporation — a fixed "
            "sum, and in return they pay you periodic interest (the 'coupon') and return your principal "
            "at a set maturity date.",
            "Bonds are generally less volatile than stocks because the payment schedule is contractual, "
            "not dependent on how well the business performs. Government bonds from stable countries are "
            "considered among the safest investments available; corporate bonds pay more but carry more "
            "risk that the issuer could default.",
            "The main risks are interest-rate risk (bond prices fall when rates rise, if you need to sell "
            "before maturity) and credit risk (the issuer failing to pay). Inflation is also a quiet risk: "
            "a fixed coupon buys less over time if prices are rising quickly.",
        ],
        'key_points': [
            "A loan you make to a government or company for regular interest.",
            "Lower volatility than stocks; used to balance a portfolio.",
            "Price moves inversely with interest rates if sold before maturity.",
            "Higher-yield ('junk') bonds trade extra return for extra default risk.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Bonds',
            'scenario': [
                "Imagine putting $10,000 into a 10-year government bond paying 5% annual interest. Left "
                "to compound by reinvesting each coupon into new bonds, that initial sum could grow to "
                "roughly $16,300 over the decade — a steady, predictable climb rather than a dramatic one.",
                "Bonds grow net worth less through spectacular gains and more through reliability: locking "
                "in a known return lets you plan around it, and layering bonds of different maturities "
                "('laddering') keeps cash coming due regularly to reinvest at current rates.",
            ],
            'strategies': [
                "Reinvest coupon payments into new bonds instead of spending them, so the interest itself "
                "starts earning interest.",
                "Ladder maturities (e.g. 2, 5, and 10-year bonds) so you're not stuck reinvesting "
                "everything at once if rates move against you.",
                "Use bonds to balance a portfolio's volatility, freeing you to hold more stocks elsewhere "
                "for growth.",
                "Match bond maturities to when you'll actually need the money, so you're not forced to "
                "sell early at a loss.",
            ],
            'caution': "Rising interest rates can reduce a bond's resale value before maturity — the "
                       "safest way to capture the stated return is to hold to maturity.",
        },
    },
    {
        'slug': 'mutual-funds-etfs',
        'title': 'Mutual Funds & ETFs',
        'icon': 'fa-layer-group',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Pooled baskets of stocks, bonds, or other assets that give instant diversification in one purchase.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-layer-group', 'label': 'Pooled Fund'},
            {'icon': 'fa-th', 'label': 'Many Underlying Assets'},
        ],
        'content': [
            "Mutual funds and ETFs (exchange-traded funds) both pool money from many investors to buy a "
            "diversified basket of underlying assets — often hundreds of stocks or bonds at once. Instead "
            "of picking individual securities, you buy a single unit that represents a slice of the whole "
            "basket.",
            "The practical difference is how they trade: mutual funds are priced and settled once a day "
            "after markets close, while ETFs trade continuously on an exchange like a stock, so their "
            "price can move throughout the day. ETFs also tend to have lower fees, especially index-tracking ones.",
            "Because a single fund can span an entire market or sector, funds are one of the easiest ways "
            "to diversify without needing to research dozens of individual companies yourself. The cost is "
            "the management fee (expense ratio), which eats into returns over time — even small differences "
            "compound significantly over decades.",
        ],
        'key_points': [
            "One purchase buys exposure to many underlying securities at once.",
            "ETFs trade all day like stocks; mutual funds price once daily.",
            "Index funds/ETFs usually have the lowest fees and match market returns.",
            "Actively managed funds charge more, aiming to beat the market — most don't, consistently.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Mutual Funds & ETFs',
            'scenario': [
                "Consider putting $300 a month into a low-cost, broad-market ETF. At a long-run average "
                "return of around 7%, that could grow to roughly $360,000 over 30 years — with no need to "
                "research individual companies, since the fund already spreads your money across hundreds "
                "of them.",
                "The growth mechanism is the same compounding as owning stocks directly, but the fund does "
                "the diversification work for you — reducing the odds that one bad company sinks your "
                "progress, while still capturing the market's overall long-term growth.",
            ],
            'strategies': [
                "Favor low-fee index funds/ETFs — a 1% annual fee difference compounds into a large gap in "
                "your ending balance over decades.",
                "Set up automatic monthly contributions so investing happens consistently, not only when "
                "you remember.",
                "Reinvest distributions automatically rather than taking them as cash.",
                "Resist switching funds chasing recent performance — consistency usually beats chasing "
                "trends.",
            ],
            'caution': "Even a diversified fund can fall in value during a downturn — diversification "
                       "reduces single-company risk, not market-wide risk.",
        },
    },
    {
        'slug': 'real-estate',
        'title': 'Real Estate',
        'icon': 'fa-home',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Owning physical property directly, earning through rental income and long-term appreciation.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-home', 'label': 'Property'},
            {'icon': 'fa-hand-holding-usd', 'label': 'Rent & Appreciation'},
        ],
        'content': [
            "Real estate investing means owning physical property — residential, commercial, or land — "
            "with the goal of generating rental income, capital appreciation, or both. Unlike stocks and "
            "bonds, it's a tangible, illiquid asset: selling can take weeks or months, not seconds.",
            "Rental property can produce steady cash flow, and mortgage leverage lets you control an asset "
            "worth far more than your initial cash outlay — amplifying both gains and losses. Property "
            "values also tend to move differently from financial markets, which can smooth out a "
            "portfolio's overall swings.",
            "The downsides are real: maintenance costs, vacancy periods, property taxes, and the effort of "
            "managing tenants (or paying someone to). Real estate is also concentrated risk — your money "
            "is tied to the fortunes of one property in one location, rather than spread across a market.",
        ],
        'key_points': [
            "Tangible asset generating rental income and/or appreciation.",
            "Illiquid — takes real time and cost to buy or sell.",
            "Leverage (mortgages) can amplify both returns and losses.",
            "Concentrated in a single property/location, unlike a diversified fund.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Real Estate',
            'scenario': [
                "Suppose you buy a $200,000 rental property with a $40,000 down payment and a mortgage for "
                "the rest. If the property appreciates 3% a year and rents cover the mortgage plus "
                "expenses, in 10 years the property might be worth roughly $270,000 — while your $40,000 "
                "down payment, thanks to the leverage of the mortgage, has captured gains on the full "
                "$200,000 value, not just your initial cash.",
                "Growth here comes from two compounding forces at once: the property's own appreciation, "
                "and the mortgage balance shrinking with each payment (partly funded by tenants' rent) — "
                "both steadily increasing your equity even if you never add more of your own cash.",
            ],
            'strategies': [
                "Use a mortgage deliberately as leverage, but keep payments comfortably covered by rental "
                "income so a vacancy doesn't force a sale.",
                "Reinvest rental cash flow into paying down the mortgage faster or into a down payment on "
                "a second property.",
                "Budget for maintenance and vacancy from the start rather than assuming rent always fully "
                "covers costs.",
                "Hold for the long term — real estate transaction costs are high, so frequent buying and "
                "selling erodes returns.",
            ],
            'caution': "Leverage amplifies losses as well as gains — a property that falls in value can "
                       "leave you owing more than it's worth if you bought with a small down payment.",
        },
    },
    {
        'slug': 'business-equity',
        'title': 'Business Equity',
        'icon': 'fa-briefcase',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Owning a stake in a private business — your own or someone else’s — outside the public markets.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-briefcase', 'label': 'Private Business'},
            {'icon': 'fa-chart-line', 'label': 'Profit Share & Exit Value'},
        ],
        'content': [
            "Business equity is ownership in a company that isn't publicly traded — your own venture, a "
            "family business, or a stake bought privately. Returns come from the business's profits "
            "(distributions or reinvested growth) and, eventually, from selling the stake or the business "
            "itself.",
            "Because there's no public market setting a daily price, valuing private equity is more art "
            "than science, and it's far less liquid than stocks — there may be no ready buyer when you "
            "want to exit. Recapitalizing or growing the business (plowing profits back in) directly "
            "affects your equity value in a way that's much more hands-on than owning a public stock.",
            "This is typically the highest-risk, highest-control asset class: you (or the owner you're "
            "investing alongside) can directly influence outcomes through decisions, but a struggling "
            "business can also lose most or all of its value with no market floor to catch it.",
        ],
        'key_points': [
            "Ownership in a private company, not traded on an exchange.",
            "Illiquid — no guaranteed buyer if you want to sell your stake.",
            "Value tied directly to the business's operating performance.",
            "Highest potential control and upside, but concentrated risk.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Business Equity',
            'scenario': [
                "Picture starting a small business with $20,000 of your own capital. If you plow back "
                "profits instead of taking them all as income, and the business is worth 3x its annual "
                "profit at sale, growing annual profit from $10,000 to $40,000 over several years could "
                "turn that initial $20,000 stake into a business worth $120,000 or more — growth driven "
                "entirely by reinvesting into the business itself.",
                "Unlike public stocks, your decisions directly move the value here: hiring well, improving "
                "margins, or expanding into a new market can change the business's worth far more directly "
                "than any single choice affects a public company's stock price.",
            ],
            'strategies': [
                "Reinvest early profits into the business (plow-back) rather than withdrawing them, to "
                "compound growth faster.",
                "Keep records and financials clean from the start — a business's saleable value depends "
                "heavily on being able to prove its numbers.",
                "Diversify personal net worth outside the business over time, since your income and this "
                "asset are otherwise both tied to the same outcome.",
                "Plan an eventual exit or valuation event (sale, buyout, next funding round) rather than "
                "treating the business as a number that only exists on paper.",
            ],
            'caution': "Private business value is illiquid and hard to verify day-to-day — a struggling "
                       "business can lose most of its value with no public market to signal the decline "
                       "early.",
        },
    },
    {
        'slug': 'fixed-term-deposits',
        'title': 'Fixed / Term Deposits',
        'icon': 'fa-piggy-bank',
        'risk': 'Very Low',
        'risk_class': 'very-low',
        'summary': 'Locking savings with a bank for a set period in exchange for a guaranteed interest rate.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-piggy-bank', 'label': 'Bank (Locked Term)'},
            {'icon': 'fa-coins', 'label': 'Guaranteed Interest'},
        ],
        'content': [
            "A fixed or term deposit (also called a GIC or CD depending on the country) is money placed "
            "with a bank for a set period — say 3, 6, or 12 months — in exchange for a guaranteed interest "
            "rate, usually higher than a regular savings account.",
            "The appeal is certainty: you know exactly what you'll earn, and in most countries deposits up "
            "to a certain amount are government-insured, making this one of the safest ways to hold money. "
            "The tradeoff is that your money is locked up — withdrawing early usually means a penalty or "
            "losing the promised rate.",
            "Because the return is fixed and modest, term deposits rarely outpace inflation by much, if at "
            "all. They're best used for money you'll need with certainty within a known timeframe — an "
            "emergency fund or a near-term goal — rather than as a long-term growth vehicle.",
        ],
        'key_points': [
            "Guaranteed interest rate for locking funds over a fixed term.",
            "Very low risk; often government-insured up to a limit.",
            "Early withdrawal usually forfeits some or all of the interest.",
            "Best for short-term savings, not long-term wealth growth.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Fixed/Term Deposits',
            'scenario': [
                "If you place $15,000 into a 12-month term deposit paying 4%, you'll have $15,600 at "
                "maturity, guaranteed. Rolling that amount into a new term deposit each year, and adding "
                "more savings along the way, turns this into a steady, low-drama savings ladder rather "
                "than a growth engine.",
                "The real net-worth benefit of term deposits isn't the modest interest itself — it's "
                "certainty: money you'll need in a known timeframe is protected from market swings, which "
                "lets you invest other money more aggressively elsewhere without needing to touch it.",
            ],
            'strategies': [
                "Ladder terms (e.g. 3, 6, and 12 months) so some money matures regularly instead of being "
                "locked all at once.",
                "Use term deposits for near-term goals and emergency funds, freeing longer-horizon money "
                "for higher-growth assets.",
                "Compare rates across banks before renewing — the difference of even 1% matters more the "
                "larger the balance.",
                "Avoid early withdrawal where possible, since breaking the term usually forfeits some or "
                "all of the promised interest.",
            ],
            'caution': "Term deposit returns rarely outpace inflation by much — treat this as capital "
                       "preservation, not a wealth-building engine on its own.",
        },
    },
    {
        'slug': 'cryptocurrency',
        'title': 'Cryptocurrency',
        'icon': 'fa-coins',
        'risk': 'Very High',
        'risk_class': 'very-high',
        'summary': 'Digital assets built on blockchain networks, trading 24/7 with no central issuer.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-link', 'label': 'Blockchain Network'},
            {'icon': 'fa-chart-line', 'label': 'Market Price (24/7)'},
        ],
        'content': [
            "Cryptocurrencies are digital assets that exist on decentralized blockchain networks rather "
            "than being issued by a government or company. Bitcoin and Ethereum are the largest by market "
            "value, but thousands of others exist with wildly different purposes and credibility.",
            "Unlike stock markets, crypto markets trade 24 hours a day, seven days a week, with no circuit "
            "breakers. Prices are driven heavily by sentiment, adoption news, and speculation rather than "
            "earnings or cash flow — there's often no underlying business generating profit to anchor a "
            "valuation.",
            "This makes crypto the most volatile major asset class: it's realistic to see 20%+ price "
            "swings in a single day. Custody is also a real risk of its own — losing access to a private "
            "key or trusting an insolvent exchange can mean losing funds entirely, with none of the "
            "protections that apply to regulated banks or brokerages.",
        ],
        'key_points': [
            "Decentralized digital assets with no earnings/cash flow to anchor value.",
            "Trades continuously; extremely volatile compared to stocks or bonds.",
            "Value driven largely by sentiment, adoption, and speculation.",
            "Self-custody and exchange risk are unique to this asset class.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Cryptocurrency',
            'scenario': [
                "Suppose you allocate $100 a month into a major cryptocurrency as a small slice of a "
                "broader portfolio. Because prices can swing 20%+ in a single day, the outcome over any "
                "given year varies enormously — the same habit could be worth much more or much less than "
                "what was put in, unlike the smoother paths typical of bonds or diversified funds.",
                "Given that volatility, growing net worth responsibly with crypto usually means treating it "
                "as a small, high-risk allocation alongside more stable assets, rather than a core holding "
                "— the goal is asymmetric upside without risking money you can't afford to lose.",
            ],
            'strategies': [
                "Keep crypto to a deliberately small percentage of overall net worth given its volatility.",
                "Use dollar-cost averaging (fixed regular purchases) rather than trying to time entry "
                "points in such a volatile market.",
                "Secure holdings properly (hardware wallets, reputable exchanges) — custody failures are a "
                "real, unique risk here.",
                "Avoid leverage/borrowing to buy more crypto — it turns already-high volatility into a much "
                "larger risk of total loss.",
            ],
            'caution': "Cryptocurrency has no earnings or cash flow anchoring its value — it can also fall "
                       "to zero in a way a diversified stock fund or government bond realistically cannot.",
        },
    },
    {
        'slug': 'money-market',
        'title': 'Money Market Instruments',
        'icon': 'fa-university',
        'risk': 'Very Low',
        'risk_class': 'very-low',
        'summary': 'Ultra-short-term, highly liquid debt used to safely park cash while it still earns something.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-university', 'label': 'Short-Term Debt Pool'},
            {'icon': 'fa-tachometer-alt', 'label': 'Quick Liquidity'},
        ],
        'content': [
            "Money market instruments are short-term debt — typically maturing in a year or less — issued "
            "by governments, banks, or highly-rated corporations. Treasury bills and money market funds are "
            "the most common ways individuals access this asset class.",
            "The goal isn't growth, it's capital preservation with modest, stable income while keeping the "
            "money accessible. Money market funds are designed to hold their value (often targeting a "
            "stable unit price) and can typically be withdrawn quickly, making them a common place to "
            "park cash between other investments.",
            "Because maturities are so short and issuers are typically high-credit-quality, the risk of "
            "loss is very low — but so is the return, which usually tracks close to prevailing short-term "
            "interest rates and rarely beats inflation by much over time.",
        ],
        'key_points': [
            "Short-term, high-quality debt instruments (e.g. treasury bills).",
            "Prioritizes safety and liquidity over growth.",
            "Common place to park cash between other investments.",
            "Returns track short-term interest rates — modest, not a growth engine.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Money Market Instruments',
            'scenario': [
                "If you park $10,000 in a money market fund yielding 4% while deciding where to invest "
                "longer-term, you'd earn roughly $400 over the year — modest, but earned safely while the "
                "money stays fully accessible, rather than sitting idle in a low/no-interest account.",
                "The net-worth role here isn't growth — it's keeping your safety net and near-term cash "
                "working at all, so every dollar is earning something even while it waits to be deployed "
                "elsewhere.",
            ],
            'strategies': [
                "Hold your emergency fund here instead of a low-interest checking account, so safety and "
                "modest return aren't a trade-off.",
                "Use it as a holding place for cash between investment decisions, rather than letting it "
                "sit uninvested.",
                "Compare yields periodically — money market rates track short-term interest rates and can "
                "shift meaningfully over time.",
                "Don't mistake the safety of money markets for it being a growth vehicle — its job is "
                "capital preservation with liquidity.",
            ],
            'caution': "Returns typically track short-term interest rates closely and rarely beat inflation "
                       "by much — this protects purchasing power more than it builds it.",
        },
    },
    {
        'slug': 'commercial-paper',
        'title': 'Commercial Paper',
        'icon': 'fa-file-signature',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'Short-term, unsecured IOUs that large corporations issue to cover near-term cash needs.',
        'diagram': [
            {'icon': 'fa-building', 'label': 'Corporation'},
            {'icon': 'fa-file-signature', 'label': 'Discounted IOU'},
            {'icon': 'fa-user', 'label': 'You (buy at a discount)'},
        ],
        'content': [
            "Commercial paper is short-term, unsecured debt that large, creditworthy corporations issue to "
            "fund immediate needs — payroll, inventory, receivables — rather than borrowing from a bank. "
            "It's sold at a discount to face value and matures anywhere from a few days up to 270 days, "
            "with the return coming from the difference between what you pay and what you're repaid.",
            "Because there's no collateral backing it, commercial paper relies entirely on the issuing "
            "company's credit standing — only well-established, financially strong corporations can issue "
            "it economically. Credit rating agencies grade issuers, and lower-rated paper has to offer a "
            "higher yield to attract buyers.",
            "It sits close to money market instruments and treasury bills on the risk spectrum: short "
            "maturities keep interest-rate exposure low, but unlike government-issued paper, there's real "
            "default risk if the issuing company runs into trouble — a risk that briefly caused real "
            "market stress during the 2008 financial crisis when investors lost confidence in some issuers.",
        ],
        'key_points': [
            "Unsecured short-term debt issued by large corporations (up to ~270 days).",
            "Sold at a discount; the discount-to-face-value gap is your return.",
            "No collateral — return depends entirely on the issuer's creditworthiness.",
            "Lower rate risk than long bonds, but real default risk unlike government paper.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Commercial Paper',
            'scenario': [
                "Suppose you buy commercial paper with a face value of $10,000 at a discounted price of "
                "$9,700, maturing in 90 days. At maturity you receive the full $10,000 — a $300 return in "
                "three months purely from the discount, without any coupon payments along the way.",
                "Held repeatedly and rolled over as each batch matures, commercial paper can function "
                "similarly to a money market holding — modest, short-term returns — but with a bit more "
                "yield in exchange for taking on issuer-specific credit risk instead of government-backed "
                "safety.",
            ],
            'strategies': [
                "Favor paper from highly-rated, well-established issuers to keep default risk low given "
                "there's no collateral behind it.",
                "Roll matured paper into new issuances to keep the return compounding rather than letting "
                "proceeds sit idle.",
                "Use it as part of a short-term cash strategy, not as a substitute for long-term growth "
                "assets.",
                "Diversify across issuers rather than concentrating in one company's paper, given the lack "
                "of collateral.",
            ],
            'caution': "Unlike government-backed instruments, commercial paper carries real default risk if "
                       "the issuing company runs into trouble — creditworthiness matters more here than "
                       "with money market or term deposits.",
        },
    },
    {
        'slug': 'retirement-accounts',
        'title': 'Retirement & Pension Accounts',
        'icon': 'fa-umbrella-beach',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'Tax-advantaged accounts — 401(k), RRSP, employer pension, superannuation — built to hold a mix of other investments until retirement.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-umbrella-beach', 'label': 'Tax-Advantaged Account'},
            {'icon': 'fa-chart-line', 'label': 'Underlying Investments Grow'},
        ],
        'content': [
            "A retirement or pension account isn't an asset class in itself — it's a wrapper that holds "
            "other investments (stocks, bonds, funds) under special tax rules. The account structure "
            "determines when and how you're taxed, not what's inside it.",
            "The appeal is the tax treatment: contributions may be tax-deductible, growth may be "
            "tax-deferred or tax-free, and some employers match a portion of what you contribute — "
            "effectively free money on top of your own savings. The exact rules vary widely by country "
            "and account type.",
            "The tradeoff is restricted access: withdrawing before a set retirement age usually triggers "
            "penalties and/or taxes, since these accounts are designed for long-term holding, not "
            "near-term spending. Missing an employer match, though, is its own quiet cost.",
        ],
        'key_points': [
            "A tax-advantaged wrapper, not an asset class — it holds other investments inside it.",
            "Tax treatment (deductible contributions, deferred growth) varies by country and account type.",
            "Employer matching, where offered, is effectively free additional return.",
            "Early withdrawal usually carries penalties — built for long-term, not near-term, access.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Retirement Accounts',
            'scenario': [
                "Imagine contributing $500 a month into a retirement account like a 401(k) or RRSP, with "
                "an employer matching half of that. Between your own contributions, the match, and "
                "long-run investment growth of around 7%, that combination could grow to well over "
                "$700,000 by retirement — a meaningfully larger number than the same contributions alone, "
                "without the employer match or tax advantage, would produce.",
                "The growth compounds on two fronts: the underlying investments (usually funds or stocks) "
                "grow the same way they would outside the account, while the tax deferral means more of "
                "each year's growth stays invested instead of being reduced by taxes along the way.",
            ],
            'strategies': [
                "Contribute at least enough to capture any full employer match — leaving it on the table "
                "is leaving free money unclaimed.",
                "Increase your contribution rate whenever your income rises, before you get used to "
                "spending the extra.",
                "Choose low-fee funds inside the account, since fees compound against you the same way "
                "returns compound for you.",
                "Leave the account untouched until retirement where possible — early withdrawals usually "
                "undo much of the tax advantage through penalties.",
            ],
            'caution': "Rules, contribution limits, and tax treatment vary significantly by country and "
                       "account type — what applies to a 401(k) may not apply to an RRSP or a pension.",
        },
    },
    {
        'slug': 'precious-metals-commodities',
        'title': 'Precious Metals & Commodities',
        'icon': 'fa-gem',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Physical or paper exposure to gold, silver, and other raw materials, often held as a hedge against inflation and currency risk.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-gem', 'label': 'Physical Metal / Commodity'},
            {'icon': 'fa-chart-line', 'label': 'Price Movement'},
        ],
        'content': [
            "Precious metals like gold and silver, and commodities more broadly, are raw materials rather "
            "than claims on a business or government. You can hold them physically (bars, coins, jewelry) "
            "or through paper instruments like ETFs that track their price.",
            "Unlike stocks or bonds, metals generate no dividend, interest, or rent — the entire return "
            "comes from price appreciation. Their traditional appeal is as a store of value during "
            "inflation or currency weakness, since they're not tied to any single country's monetary "
            "policy.",
            "Physical holdings carry their own costs and risks: storage, insurance, and authentication when "
            "buying or selling. Prices can still be volatile in the short term, driven by macroeconomic "
            "sentiment as much as by supply and demand for the metal itself.",
        ],
        'key_points': [
            "Raw materials, not a claim on a business — return comes purely from price movement.",
            "No dividend, interest, or rent; often held as an inflation/currency hedge instead.",
            "Physical holdings add storage, insurance, and authentication costs.",
            "Price is driven heavily by macroeconomic sentiment, not company or government performance.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Precious Metals & Commodities',
            'scenario': [
                "Say you buy $5,000 of gold as a hedge and hold it for 10 years during a period when "
                "inflation erodes the value of cash savings. If gold keeps pace with or outruns inflation "
                "over that period, your $5,000 preserves its real purchasing power — the win here is "
                "protection rather than the kind of outsized growth a stock portfolio might produce.",
                "Because metals generate no income of their own, any net-worth growth comes entirely from "
                "price appreciation — meaning the role this asset plays is usually stabilizing a portfolio "
                "during inflation or currency stress, rather than being the primary engine of long-term "
                "growth.",
            ],
            'strategies': [
                "Treat metals as a portfolio stabilizer/hedge, sized as a modest percentage of net worth "
                "rather than a primary holding.",
                "Prefer low-cost paper exposure (e.g. an ETF) over physical bars/coins if storage and "
                "insurance costs would eat into returns.",
                "Rebalance periodically — if metals rise sharply relative to the rest of your portfolio, "
                "trimming back locks in the gain.",
                "Avoid buying purely on short-term price momentum — the appeal of metals is long-term "
                "stability, not short-term trading.",
            ],
            'caution': "Metals produce no dividend or interest — during long stretches without inflation or "
                       "currency stress, they can lag behind income-generating assets significantly.",
        },
    },
    {
        'slug': 'reits',
        'title': 'REITs (Real Estate Investment Trusts)',
        'icon': 'fa-city',
        'risk': 'Medium',
        'risk_class': 'medium',
        'summary': 'Companies that own or finance income-producing real estate, traded on an exchange like a stock instead of owning property directly.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-city', 'label': 'REIT (Property Portfolio)'},
            {'icon': 'fa-hand-holding-usd', 'label': 'Dividends & Price Growth'},
        ],
        'content': [
            "A REIT is a company that owns, operates, or finances a portfolio of income-producing "
            "properties — offices, malls, apartments, warehouses — and trades on a public exchange like a "
            "stock. Buying a share gives you a proportional claim on the rental income and value of the "
            "whole portfolio.",
            "This solves real estate's biggest drawback: liquidity. Instead of tying up capital in one "
            "property for months while you find a buyer, you can buy or sell a REIT in seconds. Most "
            "REITs are also required to distribute the large majority of their taxable income as "
            "dividends, making them a popular income-focused holding.",
            "The tradeoff is that a REIT's price still moves with the stock market and with interest "
            "rates — often more than the value of the underlying properties would suggest day to day — so "
            "it doesn't fully replace the diversification benefit of directly-owned property.",
        ],
        'key_points': [
            "Exchange-traded exposure to real estate — liquid, unlike owning property directly.",
            "Required to distribute most taxable income as dividends, favoring income-focused investors.",
            "Price moves with the stock market and interest rates, not just underlying property values.",
            "A different risk/liquidity profile than direct real estate, despite the shared asset.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with REITs',
            'scenario': [
                "Suppose you invest $10,000 in a diversified REIT yielding 4% in dividends annually, with "
                "the share price also appreciating 3% a year. Reinvesting those dividends into more REIT "
                "shares rather than spending them, that $10,000 could grow to roughly $19,000 over 15 "
                "years — combining income and appreciation the way direct rental property does, without "
                "needing to manage a single tenant.",
                "The growth mechanism mirrors real estate's rental-income-plus-appreciation model, but "
                "liquidity means you can also rebalance or exit far more easily if your goals or the market "
                "change.",
            ],
            'strategies': [
                "Reinvest REIT dividends automatically (many brokerages support this) so income compounds "
                "instead of sitting as cash.",
                "Diversify across REIT sectors (residential, commercial, industrial) rather than betting on "
                "one property type.",
                "Treat REITs as the liquid half of a real estate allocation, especially if direct property "
                "ownership isn't practical yet.",
                "Watch interest-rate sensitivity — REIT prices often move with rate expectations, sometimes "
                "more than the underlying properties' values do.",
            ],
            'caution': "REITs still trade like stocks day-to-day, so their price can fall even when the "
                       "underlying real estate market is stable — don't expect direct-property-like price "
                       "stability.",
        },
    },
    {
        'slug': 'peer-to-peer-lending',
        'title': 'Peer-to-Peer & Private Lending',
        'icon': 'fa-handshake',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Lending directly to individuals or businesses, often through a platform, in exchange for interest — bypassing a traditional bank.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-handshake', 'label': 'Borrower (via Platform)'},
            {'icon': 'fa-coins', 'label': 'Interest Payments'},
        ],
        'content': [
            "Peer-to-peer (P2P) and private lending means acting as the lender directly — usually through "
            "an online platform that matches you with individual or small-business borrowers — rather "
            "than depositing money with a bank that lends it out on your behalf.",
            "Because you're taking on the credit risk a bank would normally absorb, yields are typically "
            "higher than savings accounts or bonds of comparable term. Spreading a loan pool across many "
            "small borrowers reduces the impact of any single default, similar to how a fund diversifies "
            "across securities.",
            "The key risk is that these loans are not government-insured deposits: if a borrower defaults, "
            "or the platform itself fails, there's no deposit insurance to fall back on. Loans are also "
            "illiquid — you generally can't withdraw before the loan term ends without a secondary market.",
        ],
        'key_points': [
            "You take on the lender's role directly, usually via a platform matching you to borrowers.",
            "Higher yields than bank deposits, compensating for the credit risk you're now bearing.",
            "Not government-insured — borrower default or platform failure is a real loss risk.",
            "Illiquid: funds are typically locked until the loan term ends.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Peer-to-Peer & Private Lending',
            'scenario': [
                "Imagine lending $5,000 spread across 100 small loans on a P2P platform at an average 9% "
                "interest rate. Even accounting for a realistic default rate on a handful of those loans, "
                "diversifying across that many borrowers could still net a return of roughly 6-7% after "
                "losses — meaningfully higher than a savings account, in exchange for taking on the credit "
                "risk directly.",
                "The net-worth growth here comes from the interest spread you're capturing by acting as the "
                "lender rather than the depositor — but that spread only holds up if losses across your "
                "loan pool stay within what the higher yield is compensating you for.",
            ],
            'strategies': [
                "Spread capital across as many individual loans as the platform allows, rather than a few "
                "large ones, to limit the damage from any single default.",
                "Reinvest repaid principal and interest into new loans to keep the money compounding "
                "instead of sitting idle.",
                "Favor platforms and loan grades with a track record, and understand the platform's own "
                "default history before committing meaningfully.",
                "Keep this as a portion of net worth you can afford to have locked up, given the lack of "
                "deposit insurance and limited liquidity.",
            ],
            'caution': "A platform failure or a spike in borrower defaults (e.g. during an economic "
                       "downturn) can erode returns quickly — the yield premium exists precisely because "
                       "this risk is real.",
        },
    },
    {
        'slug': 'employer-equity-compensation',
        'title': 'Employer Equity Compensation',
        'icon': 'fa-id-badge',
        'risk': 'High',
        'risk_class': 'high',
        'summary': 'Stock options or restricted stock units (RSUs) granted by an employer, vesting over time as part of compensation.',
        'diagram': [
            {'icon': 'fa-briefcase', 'label': 'Employer'},
            {'icon': 'fa-id-badge', 'label': 'Options / RSUs (Vesting)'},
            {'icon': 'fa-user', 'label': 'You (Own Shares)'},
        ],
        'content': [
            "Employer equity compensation — stock options or restricted stock units (RSUs) — grants you a "
            "stake in the company you work for as part of your pay package, typically vesting gradually "
            "over several years rather than being available all at once.",
            "It aligns your incentives with the company's performance and can be a significant source of "
            "wealth if the company does well, but it also concentrates risk: your income and a chunk of "
            "your net worth are tied to the fortunes of the same employer. If the company struggles, both "
            "can be affected together.",
            "Tax treatment and liquidity depend heavily on the type of grant and whether the company is "
            "public or private — options and RSUs in a private company may be effectively illiquid until "
            "an IPO or acquisition, with no guarantee either happens on any timeline.",
        ],
        'key_points': [
            "Equity granted as part of compensation, vesting gradually rather than all at once.",
            "Concentrates risk — income and equity value both depend on the same employer.",
            "Tax treatment differs by grant type (options vs. RSUs) and by jurisdiction.",
            "Illiquid until vested, and potentially until IPO/acquisition for private companies.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Employer Equity Compensation',
            'scenario': [
                "Suppose you're granted RSUs worth $40,000 vesting evenly over 4 years. If you hold the "
                "shares as they vest rather than selling immediately, and the company's stock grows 8% a "
                "year, that grant alone could be worth meaningfully more than $40,000 by the time it's "
                "fully vested and left to grow further — on top of whatever salary and other savings you're "
                "separately building.",
                "The growth here is really two things layered together: the compensation itself (equity "
                "you didn't have to buy with your own cash) and whatever the shares do afterward — meaning "
                "the biggest net-worth decision is often not whether to accept the grant, but what to do "
                "with the shares once they vest.",
            ],
            'strategies': [
                "Understand your vesting schedule and plan around it — don't assume unvested grants are "
                "money in hand.",
                "Consider selling at least a portion of vested shares to diversify, rather than letting "
                "concentration in one employer grow unchecked.",
                "Plan for the tax event at vesting (or exercise, for options) in advance so it doesn't "
                "surprise you at tax time.",
                "Treat equity comp as a bonus on top of a separate savings/investment plan, not a "
                "replacement for one.",
            ],
            'caution': "If the employer's stock falls or the company fails, both your income and this part "
                       "of your net worth can be hit at the same time — concentration risk here is real, "
                       "not theoretical.",
        },
    },
    {
        'slug': 'annuities',
        'title': 'Annuities',
        'icon': 'fa-umbrella',
        'risk': 'Low–Medium',
        'risk_class': 'low-medium',
        'summary': 'An insurance contract that converts a lump sum or series of payments into a guaranteed income stream, usually for retirement.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-umbrella', 'label': 'Insurance Company'},
            {'icon': 'fa-coins', 'label': 'Guaranteed Income Stream'},
        ],
        'content': [
            "An annuity is a contract with an insurance company: you pay a lump sum or a series of "
            "premiums, and in return the insurer guarantees you a stream of income, often for the rest of "
            "your life. It's designed to solve the risk of outliving your savings in retirement.",
            "Fixed annuities pay a guaranteed rate, behaving similarly to a bond; variable annuities tie "
            "payments to the performance of underlying investments, trading certainty for upside "
            "potential. Some also bundle in insurance features like a death benefit for beneficiaries.",
            "The tradeoffs are real: annuities are illiquid once purchased, often carry surrender charges "
            "for early withdrawal, and the guarantee is only as good as the issuing insurer's financial "
            "strength. Fees can also be higher and less transparent than other income-generating assets.",
        ],
        'key_points': [
            "An insurance contract trading a lump sum for a guaranteed (or variable) income stream.",
            "Fixed annuities behave like a bond; variable annuities tie payments to investment performance.",
            "Illiquid after purchase, often with surrender charges for early withdrawal.",
            "The guarantee is only as strong as the issuing insurer's own financial health.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Annuities',
            'scenario': [
                "Imagine converting a $100,000 lump sum into a fixed annuity at retirement that guarantees "
                "$6,000 a year for life. If you live 25 years in retirement, that's $150,000 paid out — "
                "more than the original sum — with the insurer bearing the risk of you living longer than "
                "average, in exchange for you giving up access to the lump sum itself.",
                "The 'growth' an annuity provides isn't investment return in the usual sense — it's "
                "converting an uncertain, potentially-outlived pool of savings into a guaranteed, "
                "predictable income stream, which is its own form of financial security even without "
                "market-beating returns.",
            ],
            'strategies': [
                "Compare annuity payout rates across insurers — they can vary meaningfully for the same "
                "lump sum and terms.",
                "Understand what happens to remaining value if you pass away early — some annuities offer "
                "nothing to heirs, others include a death benefit at a cost.",
                "Only annuitize a portion of retirement savings, keeping some liquid for emergencies or "
                "opportunities, since the lump sum is otherwise locked up.",
                "Check the insurer's financial strength rating — the guarantee is only as good as the "
                "company backing it.",
            ],
            'caution': "Annuities are illiquid once purchased and often carry high fees or surrender "
                       "charges — they trade flexibility for certainty, which isn't the right trade for "
                       "every situation.",
        },
    },
    {
        'slug': 'collectibles-alternative-assets',
        'title': 'Collectibles & Alternative Assets',
        'icon': 'fa-palette',
        'risk': 'Very High',
        'risk_class': 'very-high',
        'summary': 'Physical or digital items — art, watches, wine, NFTs — held for their potential to appreciate outside traditional financial markets.',
        'diagram': [
            {'icon': 'fa-user', 'label': 'You'},
            {'icon': 'fa-palette', 'label': 'Physical / Digital Item'},
            {'icon': 'fa-chart-line', 'label': 'Resale Value'},
        ],
        'content': [
            "Collectibles and alternative assets — fine art, watches, wine, rare collectibles, and more "
            "recently NFTs — are held not for any income they generate, since they typically produce none, "
            "but purely for the possibility that someone will pay more for them later.",
            "Valuation is inherently subjective: there's no earnings report or interest rate to anchor a "
            "price, only what a buyer is willing to pay at a given moment. Markets for these items are "
            "often thin, meaning it can take a long time to find a buyer at a fair price.",
            "Owning physical items adds costs unique to this asset class — authentication, storage, "
            "insurance — while digital collectibles carry their own custody risks. Prices are driven "
            "heavily by taste, trends, and speculation rather than any underlying cash flow.",
        ],
        'key_points': [
            "Generates no income — the entire return depends on reselling for more than you paid.",
            "Valuation is subjective and markets are thin, often making a fair sale slow to find.",
            "Physical items add authentication, storage, and insurance costs.",
            "Prices are driven by taste and speculation, with no cash flow to anchor a valuation.",
        ],
        'growth': {
            'title': 'Growing Your Net Worth with Collectibles & Alternative Assets',
            'scenario': [
                "Suppose you buy a piece of art for $5,000 that appreciates to $12,000 over 10 years as the "
                "artist's reputation grows. On paper that's a strong return — but unlike a stock, there's "
                "no guaranteed buyer at that price, and finding one who agrees with your $12,000 valuation "
                "might take months and cost a commission along the way.",
                "Growth in this category depends entirely on someone else's later willingness to pay more "
                "— there's no earnings report, interest payment, or rental income underneath it, which "
                "makes both the timing and size of any gain far less predictable than other asset classes.",
            ],
            'strategies': [
                "Buy only within a category you genuinely understand — valuation here depends heavily on "
                "niche expertise most people don't have.",
                "Budget for authentication, insurance, and storage costs, which quietly reduce the "
                "effective return.",
                "Treat this as a small, speculative slice of net worth, not a substitute for "
                "income-generating or liquid holdings.",
                "Be realistic about time to sell — plan for months, not days, if you need to convert a "
                "collectible back to cash.",
            ],
            'caution': "Prices are driven by taste and speculation rather than cash flow, and can fall out "
                       "of fashion — this is one of the least liquid, least predictable ways to grow net "
                       "worth on this list.",
        },
    },
]


def get_tutorial(slug):
    return next((t for t in INVESTMENT_TUTORIALS if t['slug'] == slug), None)
