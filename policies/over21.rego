package idio

default over_21 := false

default reason := "under 21"

approx_21_years_ns := ((((21 * 365) * 24) * 60) * 60) * 1000000000

over_21 if {
	time.parse_rfc3339_ns(input.birthdate)
	birth_ns := time.parse_rfc3339_ns(input.birthdate)
	time_now := time.now_ns()
	time_now - birth_ns > approx_21_years_ns	
}