print("Testing LHDN calculation logic manually...")

# Manual calculation based on your example
# November 2025 scenario

# Given data
accumulated_gross = 170000.0  # Jan-Oct total
current_gross = 17000.0       # November
future_gross = 17000.0        # December estimate

accumulated_epf = 1870.0      # Your specified value
current_epf = min(1870.0, 4000.0/12)  # Limited to 333.33
remaining_epf_annual = 4000.0 - accumulated_epf - current_epf
future_epf = min(1870.0, remaining_epf_annual)  # For December

individual_relief = 9000.0
other_reliefs = 41.65

# Calculate P (Annual Taxable Income)
total_gross = accumulated_gross + current_gross + future_gross
total_epf = accumulated_epf + current_epf + future_epf
total_reliefs = individual_relief + other_reliefs

P = total_gross - total_epf - total_reliefs

print(f"Calculation breakdown:")
print(f"Total Gross: {accumulated_gross:,.2f} + {current_gross:,.2f} + {future_gross:,.2f} = {total_gross:,.2f}")
print(f"Current EPF (limited): {current_epf:,.2f}")
print(f"Remaining EPF allowance: {remaining_epf_annual:,.2f}")
print(f"Future EPF: {future_epf:,.2f}")
print(f"Total EPF: {accumulated_epf:,.2f} + {current_epf:,.2f} + {future_epf:,.2f} = {total_epf:,.2f}")
print(f"Total Reliefs: {total_reliefs:,.2f}")
print(f"P (Taxable Income): {P:,.2f}")

# Tax calculation
# For P ≈ 191,000, falls in bracket 100,001-400,000 (24% rate)
M = 100000
R = 0.24
B_before_rebate = 10950  # Base tax for this bracket
individual_rebate = 400
B = max(0, B_before_rebate - individual_rebate)  # After rebate

annual_tax_before_rebate = (P - M) * R + B_before_rebate
annual_tax = max(0, annual_tax_before_rebate - individual_rebate)

print(f"\\nTax calculation:")
print(f"Tax bracket: {M:,} - 400,000 (Rate: {R:.1%})")
print(f"Annual tax before rebate: ({P:,.2f} - {M:,}) × {R:.1%} + {B_before_rebate:,} = {annual_tax_before_rebate:,.2f}")
print(f"Annual tax after RM{individual_rebate} rebate: {annual_tax:,.2f}")

# PCB calculation (divide by 12 months)
pcb = annual_tax / 12

print(f"\\nPCB calculation:")
print(f"PCB = {annual_tax:,.2f} ÷ 12 = {pcb:,.2f}")
print(f"Expected PCB: 2,678.30")
print(f"Difference: {abs(pcb - 2678.30):,.2f}")

if abs(pcb - 2678.30) < 1.0:
    print("✅ Perfect match!")
elif abs(pcb - 2678.30) < 50.0:
    print("✅ Very close!")
else:
    print("❌ Needs adjustment")
