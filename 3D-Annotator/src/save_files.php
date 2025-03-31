<?php
// Verifica se i file sono stati inviati correttamente
if (isset($_FILES['glbFile']) && isset($_FILES['manifestJSON'])) {
    $fileName = pathinfo($_FILES['glbFile']['name'], PATHINFO_FILENAME);
    $uploadDir = __DIR__ . "iiifmanifests/$fileName/";

    // Crea la directory se non esiste
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }

    // Salva il file GLB
    $glbPath = $uploadDir . basename($_FILES['glbFile']['name']);
    if (move_uploaded_file($_FILES['glbFile']['tmp_name'], $glbPath)) {
        echo "File GLB salvato con successo in: $glbPath\n";
    } else {
        http_response_code(500);
        echo "Errore durante il salvataggio del file GLB in: $glbPath\n";
        error_log("Errore nel salvataggio di GLB in $glbPath: " . print_r(error_get_last(), true));
        exit;
    }

    // Salva il manifest JSON
    $jsonPath = $uploadDir . basename($_FILES['manifestJSON']['name']);
    if (move_uploaded_file($_FILES['manifestJSON']['tmp_name'], $jsonPath)) {
        echo "Manifest JSON salvato con successo in: $jsonPath\n";
    } else {
        http_response_code(500);
        echo "Errore durante il salvataggio del manifest JSON in: $jsonPath\n";
        error_log("Errore nel salvataggio di JSON in $jsonPath: " . print_r(error_get_last(), true));
        exit;
    }

    http_response_code(200);
    echo "File GLB e manifest JSON salvati con successo.";
} else {
    http_response_code(400);
    echo "File non ricevuti correttamente.\n";
    error_log("Errore: file non ricevuti correttamente.");
}
?>
