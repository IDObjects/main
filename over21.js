function isOver21(dobString) {
    const dob = new Date(dobString);
    const today = new Date();
    const age21Date = new Date(dob);
    age21Date.setFullYear(dob.getFullYear() + 21);
    return today >= age21Date;
  }
  
  // Example usage:
  const input = {
    user: {
      name: "Jane Doe",
      dob: "2000-04-30"
    }
  };
  
  input.user.isOver21 = isOver21(input.user.dob);
  
  console.log(JSON.stringify(input, null, 2));