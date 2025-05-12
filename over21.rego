package over21

# is_over21 checks if a user is over 21 based on their date of birth
# Input: {"user": {"dob": "YYYY-MM-DD"}, "current_date": "YYYY-MM-DD"}
# Output: boolean indicating if user is 21 or older

default is_over21 = false

is_over21 if{
    # Parse the input date of birth
    [birth_year, birth_month, birth_day] := split(input.user.dob, "-")
    
    # Parse the current date
    [current_year, current_month, current_day] := split(input.current_date, "-")
    
    # Convert all parts to numbers
    birth_y := to_number(birth_year)
    birth_m := to_number(birth_month)
    birth_d := to_number(birth_day)
    current_y := to_number(current_year)
    current_m := to_number(current_month)
    current_d := to_number(current_day)
    
    # Calculate base age
    age := current_y - birth_y
    
    # Check if birthday hasn't occurred yet this year (month is earlier)
    current_m < birth_m
    
    # Adjust age if birthday hasn't occurred yet
    adjusted_age := age - 1
    
    # Check if adjusted age is 21 or older
    adjusted_age >= 21
}

# Case when current month is same as birth month but day is before birthday
is_over21 if {
    # Parse the input date of birth
    [birth_year, birth_month, birth_day] := split(input.user.dob, "-")
    
    # Parse the current date
    [current_year, current_month, current_day] := split(input.current_date, "-")
    
    # Convert all parts to numbers
    birth_y := to_number(birth_year)
    birth_m := to_number(birth_month)
    birth_d := to_number(birth_day)
    current_y := to_number(current_year)
    current_m := to_number(current_month)
    current_d := to_number(current_day)
    
    # Calculate base age
    age := current_y - birth_y
    
    # Check if current month is same as birth month but day is before birthday
    current_m == birth_m
    current_d < birth_d
    
    # Adjust age if birthday hasn't occurred yet
    adjusted_age := age - 1
    
    # Check if adjusted age is 21 or older
    adjusted_age >= 21
}

# Case when birthday has already occurred this year (month is later)
is_over21 if {
    # Parse the input date of birth
    [birth_year, birth_month, birth_day] := split(input.user.dob, "-")
    
    # Parse the current date
    [current_year, current_month, current_day] := split(input.current_date, "-")
    
    # Convert all parts to numbers
    birth_y := to_number(birth_year)
    birth_m := to_number(birth_month)
    birth_d := to_number(birth_day)
    current_y := to_number(current_year)
    current_m := to_number(current_month)
    current_d := to_number(current_day)
    
    # Calculate age
    age := current_y - birth_y
    
    # Check if birthday has already occurred this year (month is later)
    current_m > birth_m
    
    # Check if age is 21 or older
    age >= 21
}

# Case when birthday is today or later in the month
is_over21 if {
    # Parse the input date of birth
    [birth_year, birth_month, birth_day] := split(input.user.dob, "-")
    
    # Parse the current date
    [current_year, current_month, current_day] := split(input.current_date, "-")
    
    # Convert all parts to numbers
    birth_y := to_number(birth_year)
    birth_m := to_number(birth_month)
    birth_d := to_number(birth_day)
    current_y := to_number(current_year)
    current_m := to_number(current_month)
    current_d := to_number(current_day)
    
    # Calculate age
    age := current_y - birth_y
    
    # Check if it's the birth month and day is on or after birthday
    current_m == birth_m
    current_d >= birth_d
    
    # Check if age is 21 or older
    age >= 21
}
