<?php
require __DIR__ . '/vendor/autoload.php';

use Holiday\MalaysiaHoliday;

$holiday = new MalaysiaHoliday();
// Instead of fromAllState(), do:
$holiday = $holiday->fromState([], 2025);  // pass empty array as region

$result = $holiday->get();
print_r($result);
?>