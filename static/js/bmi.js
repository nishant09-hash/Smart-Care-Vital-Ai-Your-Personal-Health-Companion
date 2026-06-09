function calculateBMI() {
  const heightInput = document.getElementById("height");
  const weightInput = document.getElementById("weight");
  const result = document.getElementById("result");

  // parse numeric values
  const height = parseFloat(heightInput.value);
  const weight = parseFloat(weightInput.value);

  // validate
  if (isNaN(height) || isNaN(weight) || height <= 0 && height <= 200 || weight <= 0 && weight <= 200) {
    result.innerHTML = "⚠️ Please enter valid height and weight!";
    result.style.color = "darkorange";
    return;
  }

  // Convert height to meters and calculate BMI
  const heightM = height / 100;
  const bmi = (weight / (heightM * heightM)).toFixed(2);

  let category = "";
  if (bmi < 18.5) {
    category = "Underweight";
    result.style.color = "orange";
  } else if (bmi >= 18.5 && bmi <= 24.9) {
    category = "Normal Weight";
    result.style.color = "lightgreen";
  } else if (bmi >= 25 && bmi <= 29.9) {
    category = "Overweight";
    result.style.color = "goldenrod";
  } else {
    category = "Obese";
    result.style.color = "red";
  }

  result.innerHTML = `Your BMI is <b>${bmi}</b> (${category})`;
}