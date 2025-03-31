<?php
// save_annotations.php

// Connessione al database
require_once 'config.php';

// Utilizza la connessione PDO dal file di configurazione
$conn = $pdo;

// Ottieni i dati dalla richiesta
$data = json_decode(file_get_contents('php://input'), true);
$checksum = $data['checksum'];
$annotations = $data['annotations'];

try {
    // Avvia una transazione per garantire la coerenza dei dati
    $conn->beginTransaction();

    // Cancella annotazioni esistenti per il checksum specificato
    $sql_delete = "DELETE FROM annotations WHERE checksum = :checksum";
    $stmt_delete = $conn->prepare($sql_delete);
    $stmt_delete->bindParam(':checksum', $checksum);
    $stmt_delete->execute();

    // Inserisci le nuove annotazioni
    $sql_insert = "INSERT INTO annotations (checksum, x, y, z, text) VALUES (:checksum, :x, :y, :z, :text)";
    $stmt_insert = $conn->prepare($sql_insert);

    foreach ($annotations as $annotation) {
        $x = $annotation['position']['x'];
        $y = $annotation['position']['y'];
        $z = $annotation['position']['z'];
        $text = $annotation['text'];

        $stmt_insert->bindParam(':checksum', $checksum);
        $stmt_insert->bindParam(':x', $x);
        $stmt_insert->bindParam(':y', $y);
        $stmt_insert->bindParam(':z', $z);
        $stmt_insert->bindParam(':text', $text);
        $stmt_insert->execute();
    }

    // Conferma la transazione
    $conn->commit();

    http_response_code(200);
    echo json_encode(["message" => "Annotazioni salvate con successo"]);
} catch (Exception $e) {
    // In caso di errore, annulla la transazione
    $conn->rollBack();
    http_response_code(500);
    echo json_encode(["error" => "Errore durante il salvataggio delle annotazioni: " . $e->getMessage()]);
}
?>
