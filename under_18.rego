package idio

default under_18 := false

default reason := "not_under_18"

under_18 if {
	valid_birthdate
	is_too_young
}

# Helpers

valid_birthdate if {
	input.birthdate
	time.parse_rfc3339_ns(input.birthdate)
}

is_too_young if {
	birth_ns := time.parse_rfc3339_ns(input.birthdate)
	time.now_ns() - birth_ns < data.idio.approx_18_years_ns
}

reason := "birthdate_missing_or_invalid" if {
	not valid_birthdate
}

reason := "age_is_18_or_over" if {
	valid_birthdate
	not is_too_young
}