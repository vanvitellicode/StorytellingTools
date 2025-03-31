<?php
// Avvia la sessione e includi i file di configurazione necessari
session_start();
require '../src/config.php';
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Annotazione 3D - Interfaccia Principale</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <link rel="stylesheet" href="../public/css/style.css">
</head>
<body>
    <div class="container">
        <h2 class="text-center mt-4">Annotazione di Modelli 3D</h2>
        
        <?php include '../public/index.html'; ?>

        <div class="annotations mt-5">
            <h3>Annotazioni Salvate</h3>
            <table id="annotationsTable" class="table table-striped">
            <thead>
                <tr>
                    <th>PositionX</th>
                    <th>PositionY</th>
                    <th>PositionZ</th>
                    <th>Annotation</th>
                    <th>Delete</th>
                </tr>
            </thead>
            <tbody>
                <!-- Righe della tabella saranno popolate dinamicamente da viewer.js -->
            </tbody>
        </table>
        </div>
    </div>
</body>
</html>
