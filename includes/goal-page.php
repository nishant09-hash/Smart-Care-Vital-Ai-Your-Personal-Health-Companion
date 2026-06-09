<?php

declare(strict_types=1);

require_once __DIR__ . '/goal-data.php';

const MAX_WEEKLY_TARGET_LENGTH = 120;
const MAX_CHATBOT_MESSAGE_LENGTH = 400;

$catalog = getGoalCatalog();
$goal = $catalog[$goalSlug] ?? null;

if ($goal === null) {
    http_response_code(404);
    echo 'Goal page not found.';
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($goal['title']) ?> | SmartCare Vital AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/assets/css/style.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
        <a class="navbar-brand" href="/index.php">SmartCare Vital AI</a>
    </div>
</nav>

<main class="container py-4">
    <section class="mb-4">
        <h1 class="display-6"><?= htmlspecialchars($goal['title']) ?></h1>
        <p class="lead mb-0"><?= htmlspecialchars($goal['description']) ?></p>
    </section>

    <div class="row g-4 mb-4">
        <div class="col-md-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h2 class="h5">Suggested Plans</h2>
                    <ul class="mb-0">
                        <?php foreach ($goal['plans'] as $item): ?>
                            <li><?= htmlspecialchars($item) ?></li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h2 class="h5">Exercise Routines</h2>
                    <ul class="mb-0">
                        <?php foreach ($goal['routines'] as $item): ?>
                            <li><?= htmlspecialchars($item) ?></li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h2 class="h5">Health Tips</h2>
                    <ul class="mb-0">
                        <?php foreach ($goal['tips'] as $item): ?>
                            <li><?= htmlspecialchars($item) ?></li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <section class="card shadow-sm mb-4">
        <div class="card-body">
            <h2 class="h5">Track Your Goal Progress</h2>
            <form class="row g-3" data-goal-form>
                <input type="hidden" name="goal_slug" value="<?= htmlspecialchars($goalSlug) ?>">
                <div class="col-md-6">
                    <label for="targetDate" class="form-label">Target Date</label>
                    <input type="date" class="form-control" id="targetDate" name="target_date" required>
                </div>
                <div class="col-md-6">
                    <label for="weeklyTarget" class="form-label">Weekly Target</label>
                    <input type="text" class="form-control" id="weeklyTarget" name="weekly_target" maxlength="<?= MAX_WEEKLY_TARGET_LENGTH ?>" placeholder="e.g. 4 workouts / week" required>
                </div>
                <div class="col-12">
                    <button type="submit" class="btn btn-primary">Save Goal</button>
                    <span class="ms-2 small" data-goal-status></span>
                </div>
            </form>
        </div>
    </section>

    <section class="card shadow-sm">
        <div class="card-body">
            <h2 class="h5">Ask the Vital AI Chatbot</h2>
            <p class="text-muted small">Get personalized fitness guidance based on your <?= htmlspecialchars($goal['title']) ?> goal.</p>
            <div class="chat-window border rounded p-3 mb-3" data-chat-window>
                <div class="chat-message ai">Hi! Tell me your schedule and fitness level for personalized recommendations.</div>
            </div>
            <form class="d-flex gap-2" data-chat-form>
                <input type="hidden" name="goal_slug" value="<?= htmlspecialchars($goalSlug) ?>">
                <input type="text" class="form-control" name="message" maxlength="<?= MAX_CHATBOT_MESSAGE_LENGTH ?>" placeholder="Ask for a workout plan..." required>
                <button type="submit" class="btn btn-success">Send</button>
            </form>
        </div>
    </section>
</main>

<script src="/assets/js/app.js"></script>
</body>
</html>
