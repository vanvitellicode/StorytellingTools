<?php
// delete_annotation.php

// Connessione al database
require_once 'config.php';

$conn = $pdo;

// Ottieni i dati dalla richiesta
$data = json_decode(file_get_contents('php://input'), true);
$x = $data['x'];
$y = $data['y'];
$z = $data['z'];
$text = $data['text'];

try {
    // Prepara la query per eliminare l'annotazione
    $sql = "DELETE FROM annotations WHERE x = :x AND y = :y AND z = :z AND text = :text";
    $stmt = $conn->prepare($sql);
    $stmt->bindParam(':x', $x);
    $stmt->bindParam(':y', $y);
    $stmt->bindParam(':z', $z);
    $stmt->bindParam(':text', $text);
    $stmt->execute();

    if ($stmt->rowCount() > 0) {
        http_response_code(200);
        echo json_encode(["message" => "Annotazione eliminata con successo"]);
    } else {
        http_response_code(404);
        echo json_encode(["message" => "Annotazione non trovata"]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["error" => "Errore durante l'eliminazione dell'annotazione: " . $e->getMessage()]);
}
?>
