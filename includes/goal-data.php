<?php

declare(strict_types=1);

function getGoalCatalog(): array
{
    return [
        'fat-burning' => [
            'title' => 'Fat Burning',
            'description' => 'Burn calories effectively with interval training and strength routines.',
            'plans' => [
                '5-day split: HIIT, strength, mobility, steady-state cardio, active recovery.',
                'Daily calorie-aware meal planning with high-protein options.',
            ],
            'routines' => [
                '20-minute HIIT circuit: jumping jacks, squats, mountain climbers, burpees.',
                'Bodyweight strength: push-ups, lunges, planks, glute bridges.',
            ],
            'tips' => [
                'Stay hydrated and prioritize sleep to improve fat metabolism.',
                'Track heart rate zones to keep workouts efficient.',
            ],
        ],
        'cardio' => [
            'title' => 'Cardio',
            'description' => 'Improve endurance and heart health with progressive cardio sessions.',
            'plans' => [
                'Weekly progression with interval runs and low-impact endurance days.',
                'Cross-training mix: cycling, brisk walking, and stair sessions.',
            ],
            'routines' => [
                '30-minute walk-jog intervals with 1:1 work-rest ratio.',
                'Station bike: 10-minute warm-up + 6 sprint rounds + cooldown.',
            ],
            'tips' => [
                'Increase training volume gradually to avoid overuse injuries.',
                'Use talk-test pacing to monitor cardio intensity.',
            ],
        ],
        'yoga' => [
            'title' => 'Yoga',
            'description' => 'Build flexibility, balance, and mindfulness with guided yoga flows.',
            'plans' => [
                'Morning mobility flow + evening restorative stretch sequence.',
                'Weekly focus rotation: flexibility, balance, strength, and relaxation.',
            ],
            'routines' => [
                'Sun salutation rounds, warrior sequence, triangle and tree pose.',
                'Core stability flow with plank variations and controlled breath work.',
            ],
            'tips' => [
                'Pair poses with controlled breathing for better posture and calm.',
                'Avoid forcing range of motion; progress with consistency.',
            ],
        ],
        'weight-loss' => [
            'title' => 'Weight Loss',
            'description' => 'Combine balanced nutrition, activity, and consistency for sustainable results.',
            'plans' => [
                'Calorie deficit strategy with weekly progress checks.',
                'Alternating cardio and resistance sessions 5 days/week.',
            ],
            'routines' => [
                'Circuit: squats, rows, shoulder presses, plank holds, step-ups.',
                'Low-impact cardio: incline walking or cycling for 35 minutes.',
            ],
            'tips' => [
                'Use portion control and prioritize whole foods.',
                'Track non-scale wins like stamina and strength.',
            ],
        ],
    ];
}
