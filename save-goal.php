<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/goal-data.php';

const MAX_WEEKLY_TARGET_LENGTH = 120;

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['message' => 'Method not allowed.']);
    exit;
}

$payload = json_decode((string) file_get_contents('php://input'), true);
$goalSlug = (string) ($payload['goal_slug'] ?? '');
$targetDate = (string) ($payload['target_date'] ?? '');
$weeklyTarget = trim((string) ($payload['weekly_target'] ?? ''));

if (!isset(getGoalCatalog()[$goalSlug]) || $weeklyTarget === '' || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $targetDate)) {
    http_response_code(422);
    echo json_encode(['message' => 'Invalid goal input.']);
    exit;
}

try {
    $db = getDbConnection();
    $stmt = $db->prepare('INSERT INTO user_goals (goal_slug, target_date, weekly_target) VALUES (:goal_slug, :target_date, :weekly_target)');
    $stmt->execute([
        ':goal_slug' => $goalSlug,
        ':target_date' => $targetDate,
        ':weekly_target' => mb_substr($weeklyTarget, 0, MAX_WEEKLY_TARGET_LENGTH),
    ]);

    echo json_encode(['message' => 'Goal saved successfully.']);
} catch (Throwable $exception) {
    error_log('Goal save failed: ' . $exception->getMessage());
    http_response_code(500);
    echo json_encode(['message' => 'Failed to save goal. Check database configuration.']);
}
