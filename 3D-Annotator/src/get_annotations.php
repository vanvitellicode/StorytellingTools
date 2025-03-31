<?php
// get_annotations.php

// Connessione al database
require_once 'config.php';

$conn = $pdo;

// Ottieni il checksum dalla richiesta
$checksum = $_GET['checksum'];

// Recupera le annotazioni dal database
$sql = "SELECT x, y, z, text FROM annotations WHERE checksum = :checksum";
$stmt = $conn->prepare($sql);
$stmt->bindParam(":checksum", $checksum);
$stmt->execute();
$result = $stmt->fetchAll(PDO::FETCH_ASSOC);

$annotations = [];
$annotations = [];
foreach ($result as $row) {
    $annotations[] = [
        "position" => [
            "x" => (float)$row['x'],
            "y" => (float)$row['y'],
            "z" => (float)$row['z'],
        ],
        "text" => $row['text']
    ];
}

header('Content-Type: application/json');
echo json_encode(["annotations" => $annotations]);
?>
