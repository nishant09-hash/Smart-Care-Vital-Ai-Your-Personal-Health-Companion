<?php

declare(strict_types=1);

require_once __DIR__ . '/includes/config.php';
require_once __DIR__ . '/includes/goal-data.php';

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['reply' => 'Method not allowed.']);
    exit;
}

$payload = json_decode((string) file_get_contents('php://input'), true);
$message = trim((string) ($payload['message'] ?? ''));
$goalSlug = (string) ($payload['goal_slug'] ?? '');
$goalCatalog = getGoalCatalog();

if ($message === '' || !isset($goalCatalog[$goalSlug])) {
    http_response_code(422);
    echo json_encode(['reply' => 'Please provide a valid goal and message.']);
    exit;
}

$apiKey = getOpenAiApiKey();
if ($apiKey === '') {
    echo json_encode([
        'reply' => sprintf(
            'OpenAI key is not configured. For %s, start with 3 sessions weekly and increase progressively.',
            $goalCatalog[$goalSlug]['title']
        ),
    ]);
    exit;
}

$prompt = sprintf(
    'You are a helpful fitness assistant. User goal category: %s. Give safe and practical guidance in 2-4 bullet points. User asks: %s',
    $goalCatalog[$goalSlug]['title'],
    $message
);

$ch = curl_init('https://api.openai.com/v1/chat/completions');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'model' => 'gpt-4o-mini',
        'messages' => [
            ['role' => 'system', 'content' => 'You provide concise personalized fitness guidance.'],
            ['role' => 'user', 'content' => $prompt],
        ],
        'temperature' => 0.6,
    ]),
    CURLOPT_TIMEOUT => 20,
]);

$result = curl_exec($ch);
$httpCode = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
curl_close($ch);

if ($result === false || $httpCode >= 400) {
    http_response_code(502);
    echo json_encode(['reply' => 'AI assistant is temporarily unavailable. Please retry shortly.']);
    exit;
}

$decoded = json_decode($result, true);
$reply = trim((string) ($decoded['choices'][0]['message']['content'] ?? ''));

if ($reply === '') {
    $reply = 'I could not generate guidance right now. Please refine your request.';
}

echo json_encode(['reply' => $reply]);
