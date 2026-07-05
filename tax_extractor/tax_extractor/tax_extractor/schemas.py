"""
Field schemas for supported tax forms.

Each Field describes one value we want to pull out of a form. The `anchors`
are label fragments that appear ON the form near the value; the positional
parser uses them to locate the right number. `kind` controls how the raw
string is cleaned (money -> float, text -> stripped string, etc.).

The 1040 schema deliberately anchors on *label text* rather than line
numbers, because the IRS renumbers 1040 lines between tax years. Anchoring on
"adjusted gross income" survives a renumber; anchoring on "line 11" does not.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

FieldKind = Literal["money", "text", "ssn", "ein", "checkbox", "code_amount"]


@dataclass
class Field:
    key: str                      # machine name used in output
    label: str                    # human label for the spreadsheet
    anchors: list[str]            # lowercase text fragments to search for on the form
    kind: FieldKind = "money"
    # If set, only accept a value found to the RIGHT of / BELOW the anchor
    # within this many points. Tuned loosely; the parser falls back if empty.
    max_dx: float = 320.0
    max_dy: float = 26.0
    # Per-field override of the form's layout ("grid" = value below the label,
    # "row" = value to the right). None means use the form's layout. Lets a
    # single form mix both (e.g. K-1: grid for the party info, row for the
    # numbered income boxes).
    layout: str | None = None
    # Multi-word text value sitting on the line(s) directly below the label,
    # e.g. a name/address block. Uses the column-restricted name extractor.
    name_block: bool = False


@dataclass
class FormSchema:
    form_type: str
    # Phrases that, if present in the document text, identify this form type.
    detect: list[str]
    fields: list[Field] = field(default_factory=list)
    # "grid": value sits BELOW the label, left-aligned to the box (W-2 style).
    # "row":  value sits to the RIGHT of the label on the same line (1040 style).
    layout: str = "grid"


# --------------------------------------------------------------------------- #
# W-2
# --------------------------------------------------------------------------- #
W2 = FormSchema(
    form_type="W-2",
    detect=["wage and tax statement", "form w-2", "w-2 wage"],
    fields=[
        Field("employee_ssn", "Employee SSN (box a)",
              ["employee's social security", "a employee"], kind="ssn"),
        Field("employer_ein", "Employer EIN (box b)",
              ["employer identification number", "b employer"], kind="ein"),
        Field("employer_name", "Employer name (box c)",
              ["employer's name", "c employer"], kind="text", max_dy=60),
        Field("employee_name", "Employee name (box e)",
              ["employee's first name", "e employee", "employee's name"],
              kind="text", max_dy=60),
        Field("box1_wages", "Box 1 — Wages, tips, other comp.",
              ["wages, tips, other comp", "1 wages"]),
        Field("box2_fed_withheld", "Box 2 — Federal income tax withheld",
              ["federal income tax withheld", "2 federal"]),
        Field("box3_ss_wages", "Box 3 — Social security wages",
              ["social security wages", "3 social"]),
        Field("box4_ss_tax", "Box 4 — Social security tax withheld",
              ["social security tax withheld", "4 social"]),
        Field("box5_medicare_wages", "Box 5 — Medicare wages and tips",
              ["medicare wages and tips", "5 medicare"]),
        Field("box6_medicare_tax", "Box 6 — Medicare tax withheld",
              ["medicare tax withheld", "6 medicare"]),
        Field("box7_ss_tips", "Box 7 — Social security tips",
              ["social security tips", "7 social"]),
        Field("box8_allocated_tips", "Box 8 — Allocated tips",
              ["allocated tips", "8 allocated"]),
        Field("box10_dependent_care", "Box 10 — Dependent care benefits",
              ["dependent care benefits", "10 dependent"]),
        Field("box11_nonqualified", "Box 11 — Nonqualified plans",
              ["nonqualified plans", "11 nonqualified"]),
        # Box 12 a-d are code+amount pairs handled specially by the parser.
        Field("box12", "Box 12 (codes & amounts)",
              ["12a", "see instructions for box 12"], kind="code_amount",
              max_dy=80),
        Field("box15_state", "Box 15 — State",
              ["15 state", "employer's state id"], kind="text"),
        Field("box16_state_wages", "Box 16 — State wages, tips, etc.",
              ["state wages, tips", "16 state"]),
        Field("box17_state_tax", "Box 17 — State income tax",
              ["state income tax", "17 state"]),
        Field("box18_local_wages", "Box 18 — Local wages, tips, etc.",
              ["local wages, tips", "18 local"]),
        Field("box19_local_tax", "Box 19 — Local income tax",
              ["local income tax", "19 local"]),
        Field("box20_locality", "Box 20 — Locality name",
              ["locality name", "20 locality"], kind="text"),
    ],
)

# --------------------------------------------------------------------------- #
# 1040  (label-anchored; survives line-number changes across tax years)
# --------------------------------------------------------------------------- #
F1040 = FormSchema(
    form_type="1040",
    detect=["u.s. individual income tax return", "form 1040", "1040 (20"],
    layout="row",
    fields=[
        Field("wages", "Wages (W-2 box 1)",
              ["total amount from form(s) w-2", "wages, salaries, tips"]),
        Field("taxable_interest", "Taxable interest",
              ["taxable interest"]),
        Field("ordinary_dividends", "Ordinary dividends",
              ["ordinary dividends"]),
        Field("ira_pensions", "IRA / pensions & annuities (taxable)",
              ["pensions and annuities", "ira distributions"]),
        Field("social_security_benefits", "Social security benefits (taxable)",
              ["social security benefits"]),
        Field("capital_gain", "Capital gain or (loss)",
              ["capital gain or (loss)"]),
        Field("total_income", "Total income",
              ["this is your total income"]),
        Field("adjustments", "Adjustments to income",
              ["adjustments to income"]),
        Field("agi", "Adjusted gross income (AGI)",
              ["adjusted gross income"]),
        Field("deduction", "Standard or itemized deduction",
              ["standard deduction or itemized"]),
        Field("taxable_income", "Taxable income",
              ["this is your taxable income"]),
        Field("tax", "Tax",
              ["tax (see instructions)"]),
        Field("total_tax", "Total tax",
              ["this is your total tax"]),
        Field("fed_withholding", "Federal income tax withheld (total)",
              ["federal income tax withheld"]),
        Field("total_payments", "Total payments",
              ["these are your total payments"]),
        Field("overpayment", "Overpayment / refund",
              ["this is the amount you overpaid", "amount you overpaid"]),
        Field("amount_owed", "Amount you owe",
              ["amount you owe"]),
    ],
)

# --------------------------------------------------------------------------- #
# Schedule C — Profit or Loss From Business (row layout)
# --------------------------------------------------------------------------- #
SCHED_C = FormSchema(
    form_type="Schedule C",
    detect=["profit or loss from business", "schedule c (form 1040)",
            "schedule c"],
    layout="row",
    fields=[
        Field("proprietor_name", "Name of proprietor",
              ["name of proprietor"], kind="text", max_dy=40),
        Field("ssn", "Social security number (SSN)",
              ["social security number", "ssn"], kind="ssn"),
        Field("principal_business", "Principal business or profession",
              ["principal business or profession"], kind="text", max_dy=40),
        Field("business_name", "Business name",
              ["business name"], kind="text", max_dy=40),
        Field("ein", "Employer ID number (EIN)",
              ["employer id number", "employer identification number"],
              kind="ein"),
        Field("gross_receipts", "Gross receipts or sales (line 1)",
              ["gross receipts or sales"]),
        Field("returns_allowances", "Returns and allowances (line 2)",
              ["returns and allowances"]),
        Field("cost_of_goods", "Cost of goods sold (line 4)",
              ["cost of goods sold"]),
        Field("gross_profit", "Gross profit (line 5)",
              ["gross profit"]),
        Field("gross_income", "Gross income (line 7)",
              ["gross income"]),
        Field("total_expenses", "Total expenses (line 28)",
              ["total expenses before expenses for business use",
               "total expenses"]),
        Field("net_profit", "Net profit or (loss) (line 31)",
              ["net profit or (loss)"]),
    ],
)

# --------------------------------------------------------------------------- #
# Schedule E — Supplemental Income and Loss (row layout)
# --------------------------------------------------------------------------- #
SCHED_E = FormSchema(
    form_type="Schedule E",
    detect=["supplemental income and loss", "schedule e (form 1040)",
            "schedule e"],
    layout="row",
    fields=[
        Field("total_rents", "Total rents received (line 3)",
              ["total amounts reported on line 3", "rents received"]),
        Field("total_royalties", "Total royalties received (line 4)",
              ["total amounts reported on line 4", "royalties received"]),
        Field("total_expenses", "Total expenses (line 20)",
              ["total expenses"]),
        Field("depreciation", "Depreciation expense or depletion (line 18)",
              ["depreciation expense or depletion"]),
        Field("income_each_property", "Income (line 21)",
              ["income. subtract", "income or (loss)"]),
        Field("total_income_loss", "Total income or (loss) (line 26 / 41)",
              ["total rental real estate and royalty income",
               "total income or (loss)"]),
    ],
)

# --------------------------------------------------------------------------- #
# Schedule K-1 — Partner's / Shareholder's / Beneficiary's share (row layout)
# --------------------------------------------------------------------------- #
# Default layout is "row" (Part III income boxes put the amount to the right of
# the numbered label). Part I/II party info sits BELOW its label, so those
# fields override to "grid". Anchors use label text, which is stable across the
# 1065 / 1120-S / 1041 variants where the wording is shared.
SCHED_K1 = FormSchema(
    form_type="Schedule K-1",
    detect=["schedule k-1", "partner's share of income",
            "shareholder's share of income", "beneficiary's share of income"],
    layout="row",
    fields=[
        # --- Part I / II: parties (value below the label) ---
        Field("entity_name", "Entity name (partnership / S-corp / estate)",
              ["partnership's name, address", "corporation's name, address",
               "name, address, city, state"],
              kind="text", layout="grid", name_block=True, max_dy=44),
        Field("entity_ein", "Entity EIN",
              ["partnership's employer identification number",
               "corporation's employer identification number",
               "employer identification number"],
              kind="ein", layout="grid", max_dy=24),
        Field("recipient_name", "Partner / shareholder / beneficiary name",
              ["partner's name, address", "shareholder's name, address",
               "beneficiary's name, address", "partner's name"],
              kind="text", layout="grid", name_block=True, max_dy=44),
        Field("recipient_id", "Partner / shareholder TIN",
              ["partner's ssn or tin", "shareholder's identifying number",
               "partner's identifying number", "partner's ssn",
               "identifying number"],
              kind="ssn", layout="grid", max_dy=24),
        # --- Part III: numbered income / deduction boxes (amount to the right) ---
        Field("ordinary_business_income", "Ordinary business income (box 1)",
              ["ordinary business income"]),
        Field("net_rental_real_estate", "Net rental real estate income (box 2)",
              ["net rental real estate income"]),
        Field("other_net_rental", "Other net rental income (box 3)",
              ["other net rental income"]),
        Field("guaranteed_payments", "Guaranteed payments (box 4)",
              ["guaranteed payments"]),
        Field("interest_income", "Interest income (box 5)",
              ["interest income"]),
        Field("ordinary_dividends", "Ordinary dividends (box 6a)",
              ["ordinary dividends"]),
        Field("qualified_dividends", "Qualified dividends (box 6b)",
              ["qualified dividends"]),
        Field("royalties", "Royalties (box 7)",
              ["royalties"]),
        Field("net_st_capital_gain", "Net short-term capital gain (box 8)",
              ["net short-term capital gain"]),
        Field("net_lt_capital_gain", "Net long-term capital gain (box 9a)",
              ["net long-term capital gain"]),
        Field("section_1231_gain", "Net section 1231 gain (box 10)",
              ["net section 1231 gain"]),
        Field("other_income", "Other income (loss) (box 11)",
              ["other income (loss)"]),
        Field("section_179", "Section 179 deduction (box 12)",
              ["section 179 deduction"]),
        Field("other_deductions", "Other deductions (box 13)",
              ["other deductions"]),
        Field("self_employment_earnings", "Self-employment earnings (box 14)",
              ["self-employment earnings"]),
        Field("distributions", "Distributions (box 19)",
              ["distributions"]),
        Field("ending_capital", "Ending capital account",
              ["ending capital account", "ending capital"]),
    ],
)

# --------------------------------------------------------------------------- #
# 1099 family (grid layout — boxed amounts)
# --------------------------------------------------------------------------- #
F1099_NEC = FormSchema(
    form_type="1099-NEC",
    detect=["1099-nec", "nonemployee compensation"],
    layout="grid",
    fields=[
        Field("payer_name", "Payer's name",
              ["payer's name"], kind="text", max_dy=60),
        Field("payer_tin", "Payer's TIN", ["payer's tin"], kind="ein"),
        Field("recipient_name", "Recipient's name",
              ["recipient's name"], kind="text", max_dy=60),
        Field("recipient_tin", "Recipient's TIN",
              ["recipient's tin"], kind="ssn"),
        Field("box1_nonemployee_comp", "Box 1 — Nonemployee compensation",
              ["nonemployee compensation", "1 nonemployee"]),
        Field("box4_fed_withheld", "Box 4 — Federal income tax withheld",
              ["federal income tax withheld", "4 federal"]),
        Field("state_tax_withheld", "State tax withheld",
              ["state tax withheld"]),
    ],
)

F1099_MISC = FormSchema(
    form_type="1099-MISC",
    detect=["1099-misc", "miscellaneous information", "miscellaneous income"],
    layout="grid",
    fields=[
        Field("payer_name", "Payer's name",
              ["payer's name"], kind="text", max_dy=60),
        Field("recipient_tin", "Recipient's TIN",
              ["recipient's tin"], kind="ssn"),
        Field("box1_rents", "Box 1 — Rents", ["1 rents", "rents"]),
        Field("box2_royalties", "Box 2 — Royalties",
              ["2 royalties", "royalties"]),
        Field("box3_other_income", "Box 3 — Other income",
              ["3 other income", "other income"]),
        Field("box4_fed_withheld", "Box 4 — Federal income tax withheld",
              ["federal income tax withheld", "4 federal"]),
    ],
)

F1099_INT = FormSchema(
    form_type="1099-INT",
    detect=["1099-int", "interest income"],
    layout="grid",
    fields=[
        Field("payer_name", "Payer's name",
              ["payer's name"], kind="text", max_dy=60),
        Field("recipient_tin", "Recipient's TIN",
              ["recipient's tin"], kind="ssn"),
        Field("box1_interest_income", "Box 1 — Interest income",
              ["1 interest income", "interest income"]),
        Field("box2_early_withdrawal", "Box 2 — Early withdrawal penalty",
              ["early withdrawal penalty"]),
        Field("box3_treasury_interest",
              "Box 3 — Interest on U.S. Savings Bonds/Treasury",
              ["interest on u.s. savings bonds", "savings bonds and treas"]),
        Field("box4_fed_withheld", "Box 4 — Federal income tax withheld",
              ["federal income tax withheld", "4 federal"]),
    ],
)

F1099_DIV = FormSchema(
    form_type="1099-DIV",
    detect=["1099-div", "dividends and distributions"],
    layout="grid",
    fields=[
        Field("payer_name", "Payer's name",
              ["payer's name"], kind="text", max_dy=60),
        Field("recipient_tin", "Recipient's TIN",
              ["recipient's tin"], kind="ssn"),
        Field("box1a_ordinary_dividends", "Box 1a — Total ordinary dividends",
              ["total ordinary dividends", "1a total"]),
        Field("box1b_qualified_dividends", "Box 1b — Qualified dividends",
              ["qualified dividends", "1b qualified"]),
        Field("box2a_capital_gain", "Box 2a — Total capital gain distr.",
              ["total capital gain distr", "2a total"]),
        Field("box4_fed_withheld", "Box 4 — Federal income tax withheld",
              ["federal income tax withheld", "4 federal"]),
    ],
)

F1099_R = FormSchema(
    form_type="1099-R",
    detect=["1099-r", "distributions from pensions", "annuities, retirement"],
    layout="grid",
    fields=[
        Field("payer_name", "Payer's name",
              ["payer's name"], kind="text", max_dy=60),
        Field("recipient_tin", "Recipient's TIN",
              ["recipient's tin"], kind="ssn"),
        Field("box1_gross_distribution", "Box 1 — Gross distribution",
              ["gross distribution", "1 gross"]),
        Field("box2a_taxable_amount", "Box 2a — Taxable amount",
              ["taxable amount", "2a taxable"]),
        Field("box4_fed_withheld", "Box 4 — Federal income tax withheld",
              ["federal income tax withheld", "4 federal"]),
        Field("box7_distribution_code", "Box 7 — Distribution code(s)",
              ["distribution", "7 distribution"], kind="text"),
    ],
)

# Order matters for tie-breaking in detect_form_type: most specific first.
SCHEMAS: dict[str, FormSchema] = {
    "W-2": W2,
    "1099-NEC": F1099_NEC,
    "1099-MISC": F1099_MISC,
    "1099-INT": F1099_INT,
    "1099-DIV": F1099_DIV,
    "1099-R": F1099_R,
    "Schedule C": SCHED_C,
    "Schedule E": SCHED_E,
    "Schedule K-1": SCHED_K1,
    "1040": F1040,
}


def detect_form_type(text: str) -> str | None:
    """Return 'W-2' or '1040' based on phrases in the document text."""
    low = text.lower()
    # Score each schema by how many of its detect phrases appear.
    best, best_score = None, 0
    for name, schema in SCHEMAS.items():
        score = sum(1 for p in schema.detect if p in low)
        if score > best_score:
            best, best_score = name, score
    return best
