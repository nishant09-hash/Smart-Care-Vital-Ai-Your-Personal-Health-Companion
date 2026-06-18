<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/goal-data.php';

$goalCatalog = getGoalCatalog();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartCare Vital AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="/assets/css/style.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">
        <a class="navbar-brand" href="/index.php">SmartCare Vital AI</a>
    </div>
</nav>

<header class="hero-section text-white py-5 mb-4">
    <div class="container">
        <h1 class="display-5 fw-bold">Your Personal Health Companion</h1>
        <p class="lead mb-0">Set, track, and achieve fitness goals with guided routines and AI support.</p>
    </div>
</header>

<main class="container pb-5">
    <section>
        <h2 class="h4 mb-3">Choose Your Goal Category</h2>
        <div class="row g-4">
            <?php foreach ($goalCatalog as $slug => $goal): ?>
                <div class="col-sm-6 col-lg-3">
                    <article class="card h-100 shadow-sm">
                        <div class="card-body d-flex flex-column">
                            <h3 class="h5"><?= htmlspecialchars($goal['title']) ?></h3>
                            <p class="small text-muted"><?= htmlspecialchars($goal['description']) ?></p>
                            <a class="btn btn-outline-primary mt-auto" href="/<?= htmlspecialchars($slug) ?>.php">Explore</a>
                        </div>
                    </article>
                </div>
            <?php endforeach; ?>
        </div>
    </section>
</main>
</body>
</html>
