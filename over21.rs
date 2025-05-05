use chrono::{NaiveDate, Utc};

fn is_over_21(dob_string: &str) -> bool {
    let dob = NaiveDate::parse_from_str(dob_string, "%Y-%m-%d").expect("Invalid date format");
    let today = Utc::today().naive_utc();
    let age_21_date = dob.with_year(dob.year() + 21).expect("Invalid date calculation");
    today >= age_21_date
}

fn main() {
    let input = serde_json::json!({
        "user": {
            "name": "Jane Doe",
            "dob": "2000-04-30"
        }
    });

    let user = input["user"].as_object().expect("Invalid user data");
    let dob = user["dob"].as_str().expect("Invalid date of birth");
    
    let is_over_21 = is_over_21(dob);
    input["user"]["is_over_21"] = serde_json::Value::Bool(is_over_21);

    println!("{}", serde_json::to_string_pretty(&input).unwrap());
}