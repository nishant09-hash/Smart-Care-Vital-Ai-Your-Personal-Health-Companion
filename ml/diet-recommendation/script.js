(function () {
	const form = document.getElementById('dietForm');
	const nameInput = document.getElementById('name');
	const ageInput = document.getElementById('age');
	const heightInput = document.getElementById('height');
	const weightInput = document.getElementById('weight');
	const bmiInput = document.getElementById('bmi');
	const goalInput = document.getElementById('goal');
	const resultEl = document.getElementById('result');
	const resetBtn = document.getElementById('resetBtn');
	const dietTypeInput = document.getElementById('dietType');
	const useAICheck = document.getElementById('useAI');
	const useAIText = document.getElementById('useAItext');

	// model will be loaded from model.json if present. Also try to load label_map.json
	let model = null;
	let labelMap = null;
	if (useAICheck) useAICheck.disabled = true;
	if (useAIText) useAIText.textContent = 'Loading AI model...';

	// load model.json
	fetch('model.json').then(res => {
		if (!res.ok) throw new Error('No model');
		return res.json();
	}).then(j => {
		model = j;
		console.log('Loaded model.json', model);
		// try to load label_map.json (optional)
		return fetch('label_map.json');
	}).then(res => {
		if (!res || !res.ok) return null;
		return res.json();
	}).then(map => {
		if (map) {
			labelMap = map;
			console.log('Loaded label_map.json', labelMap);
		}
		if (useAIText) useAIText.textContent = 'Use AI recommendation (model loaded)';
		if (useAICheck) useAICheck.disabled = false;
	}).catch(() => {
		console.log('No model.json or label_map.json found — UI will use rule-based fallback');
		if (useAIText) useAIText.textContent = 'Use AI recommendation (model not found)';
		if (useAICheck) useAICheck.disabled = true;
	});

	// ✅ Calculate BMI dynamically
	function computeBMI() {
		const h = parseFloat(heightInput.value);
		const w = parseFloat(weightInput.value);
		if (h > 0 && w > 0) {
			const m = h / 100;
			const bmi = w / (m * m);
			bmiInput.value = bmi.toFixed(1);
			return bmi;
		}
		bmiInput.value = '';
		return null;
	}

	heightInput.addEventListener('input', computeBMI);
	weightInput.addEventListener('input', computeBMI);

	resetBtn.addEventListener('click', () => {
		form.reset();
		bmiInput.value = '';
		resultEl.innerHTML = '';
	});

	form.addEventListener('submit', function (e) {
		e.preventDefault();

		const name = nameInput.value.trim() || 'User';
		const age = parseInt(ageInput.value, 10) || 0;
		const height = parseFloat(heightInput.value);
		const weight = parseFloat(weightInput.value);
		let bmi = parseFloat(bmiInput.value);
	const goal = goalInput.value;
	let dietType = dietTypeInput.value;
	const useAI = useAICheck && useAICheck.checked;

		if ((!height || !weight) && !bmi) {
			resultEl.innerHTML = '<p>Please provide height and weight (or BMI).</p>';
			return;
		}


		if (!bmi) bmi = computeBMI();

		// If model is loaded and user opted-in, try to predict dietType using the tree
		if (useAI && model) {
			try {
				const features = { age };
				// model.feature_names may include different names; try to map
				const mapped = {};
				model.feature_names.forEach(fn => {
					mapped[fn] = features[fn] !== undefined ? features[fn] : (fn === 'age' ? age : 0);
				});
				const classIdx = evalTree(model.tree, mapped);
				const predicted = model.class_names[classIdx] || dietType;
				// map numeric/class token to friendly name via labelMap if available
				let friendly = predicted;
				try {
					const key = String(predicted);
					if (labelMap && labelMap[key]) friendly = labelMap[key];
					else if (/^\d+$/.test(key)) friendly = 'Diet ' + key;
				} catch (e) {
					// noop
				}
				dietType = String(friendly);
			} catch (err) {
				console.warn('AI prediction failed, falling back to rules', err);
			}
		}

		const plan = generatePlan({ name, age, height, weight, bmi, goal, dietType });

		resultEl.innerHTML = plan;
		window.scrollTo({ top: resultEl.offsetTop - 20, behavior: 'smooth' });
	});

	// ✅ Generate diet plan based on goal + diet type
	function generatePlan({ name, age, height, weight, bmi, goal, dietType }) {
		const activityFactor = 1.2;
		const maintenance = Math.round(24 * (weight || 70) * activityFactor);

		let targetCalories = maintenance;
		let macroNotes = '';
		let description = '';
		let meals = [];

		// ❌ BUG: You wrote (switch(goal, dietType)) — that only checks dietType.
		// ✅ FIX: Use switch(goal)
		switch (goal) {
			case 'weightloss':
				targetCalories = maintenance - 500;
				description = 'Weight loss: moderate calorie deficit with balanced macros.';
				macroNotes = 'Protein ~25-30%, Carbs ~40-45%, Fats ~25-30%';
				meals = sampleMeals('weightloss', dietType);
				break;
			case 'weightgain':
				targetCalories = maintenance + 500;
				description = 'Weight gain: calorie surplus and adequate protein to build lean mass.';
				macroNotes = 'Protein ~20-25%, Carbs ~50%, Fats ~25-30%';
				meals = sampleMeals('weightgain', dietType);
				break;
			case 'fatloss':
				targetCalories = maintenance - 400;
				description = 'Fat loss: calorie deficit with higher protein to preserve muscle.';
				macroNotes = 'Protein ~30%, Carbs ~35-40%, Fats ~25-30%';
				meals = sampleMeals('fatloss', dietType);
				break;
			case 'musclebuild':
				targetCalories = maintenance + 300;
				description = 'Muscle build: slight surplus and high protein, combined with resistance training.';
				macroNotes = 'Protein ~30-35%, Carbs ~40-45%, Fats ~20-25%';
				meals = sampleMeals('musclebuild', dietType);
				break;
			case 'healthydiet':
			default:
				targetCalories = maintenance;
				description = 'Healthy diet: balanced calories and variety of nutrients.';
				macroNotes = 'Protein ~20-25%, Carbs ~45-50%, Fats ~25-30%';
				meals = sampleMeals('healthydiet', dietType);
				break;
		}

		if (targetCalories < 1100) targetCalories = 1100;

		const bmiCategory = getBMICategory(bmi);

		let html = `
			<h2>Hi ${escapeHtml(name)} — Recommended Daily Plan</h2>
			<div class="meta">Age: ${age || '—'} • Height: ${height} cm • Weight: ${weight} kg</div>
			<div class="meta">BMI: ${bmi.toFixed(1)} (${bmiCategory})</div>
			<div class="meta">Estimated maintenance: ${maintenance} kcal • Target: <strong>${targetCalories} kcal</strong></div>
			<p>${escapeHtml(description)}</p>
			<div class="plan"><strong>Macro guidance:</strong> ${escapeHtml(macroNotes)}</div>
			<div class="plan"><strong>Diet Type:</strong> ${escapeHtml(dietType.toUpperCase())}</div>
			<div class="plan"><strong>Sample daily meals:</strong><ul>`;

		meals.forEach(meal => {
			html += `<li><strong>${escapeHtml(meal.name)}:</strong> ${escapeHtml(meal.desc)}</li>`;
		});

		html += `</ul></div>
		<p style="margin-top:10px;color:#374151;font-size:0.95rem;">Tips: Stay hydrated, prefer whole foods, include vegetables at each meal, and match activity to goal. For tailored meal plans consult a dietitian.</p>`;

		return html;
	}

	function getBMICategory(bmi) {
		if (!bmi || isNaN(bmi)) return '—';
		if (bmi < 18.5) return 'Underweight';
		if (bmi < 25) return 'Normal';
		if (bmi < 30) return 'Overweight';
		return 'Obese';
	}

	// ✅ Differentiate Veg / Non-Veg
	function sampleMeals(goal, dietType) {
		const veg = {
			breakfast: { name: 'Breakfast', desc: 'Oats 60 g cooked in milk 250 ml, banana 1 medium, and almonds 10 g.' },
			lunch: { name: 'Lunch', desc: 'Paneer/tofu curry 120 g, brown rice 150 g cooked, and salad 120 g.' },
			dinner: { name: 'Dinner', desc: 'Dal 300 ml (about 1.5 cups), 2 medium roti (30 g flour each), mixed veggies 150 g, and curd 150 ml.' },
			snack: { name: 'Snack', desc: '1 medium fruit (apple/guava) or sprouts 100 g.' },
			pre: { name: 'Pre-Workout', desc: 'Banana 1 medium, black coffee 150 ml, and roasted chana 25 g.' },
			post: { name: 'Post-Workout', desc: 'Whey protein 1 scoop (30 g) in water 250 ml, or paneer 100 g.' }
		};

		const nonveg = {
			breakfast: { name: 'Breakfast', desc: '2 whole eggs + 2 egg whites, oats 50 g cooked in milk 200 ml, and 1 medium fruit.' },
			lunch: { name: 'Lunch', desc: 'Grilled chicken/fish 150 g, rice 180 g cooked, and vegetables 150 g.' },
			dinner: { name: 'Dinner', desc: 'Chicken curry 150 g or fish 170 g, 2 medium roti, and salad 120 g.' },
			snack: { name: 'Snack', desc: '2 boiled eggs or mixed nuts 20 g.' },
			pre: { name: 'Pre-Workout', desc: 'Banana 1 medium, black coffee 150 ml, and 1 boiled egg.' },
			post: { name: 'Post-Workout', desc: 'Whey protein 1 scoop (30 g) in water 250 ml, or 3 egg whites + 1 whole egg.' }
		};

		const food = dietType === 'nonveg' ? nonveg : veg;

		// Modify meals slightly depending on goal
		switch (goal) {
			case 'weightloss':
			case 'fatloss':
				return [food.breakfast, food.lunch, food.snack, food.dinner, food.pre, food.post];
			case 'weightgain':
			case 'musclebuild':
				return [food.breakfast, food.snack, food.lunch, food.pre, food.dinner, food.post];
			case 'healthydiet':
			default:
				return [food.breakfast, food.lunch, food.dinner, food.snack];
		}
	}

	function escapeHtml(str) {
		if (!str && str !== 0) return '';
		return String(str)
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');
	}


	// Evaluate the exported JSON tree to return a class index
	function evalTree(node, features) {
		if (!node) throw new Error('Invalid tree node');
		if (node.is_leaf) return node.class;
		const feat = node.feature;
		const val = features[feat];
		if (val === undefined) throw new Error('Missing feature: ' + feat);
		if (val <= node.threshold) return evalTree(node.left, features);
		return evalTree(node.right, features);
	}
})();
