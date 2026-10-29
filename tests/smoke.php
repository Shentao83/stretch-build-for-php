<?php
// SPDX-License-Identifier: MIT
// Synthetic checks only: no application bootstrap, database or external network.
error_reporting(E_ALL);
set_error_handler(function ($severity, $message, $file, $line) {
    throw new ErrorException($message, 0, $severity, $file, $line);
});
function check($condition, $message) {
    if (!$condition) {
        throw new RuntimeException($message);
    }
}
check(PHP_VERSION === '7.4.33', 'Unexpected PHP version');
check(ini_get('session.upload_progress.enabled') === '0', 'Upload progress must be disabled');
$required = array('json', 'session', 'dom', 'SimpleXML', 'xml', 'xmlreader',
    'xmlwriter', 'xsl', 'soap', 'xmlrpc', 'bcmath', 'calendar', 'exif',
    'fileinfo', 'ftp', 'gd', 'gettext', 'iconv', 'intl', 'ldap', 'mbstring',
    'mysqli', 'PDO', 'pdo_mysql', 'openssl', 'curl', 'zlib', 'sodium', 'zip',
    'FFI', 'Phar', 'pcntl', 'posix', 'shmop', 'sockets', 'sysvmsg', 'sysvsem',
    'sysvshm', 'igbinary', 'msgpack', 'imagick', 'memcache', 'memcached');
foreach ($required as $name) {
    check(extension_loaded($name), 'Missing extension: ' . $name);
}
check(extension_loaded('Zend OPcache'), 'Missing OPcache');
check(INTL_ICU_VERSION === '65.1', 'Unexpected ICU');
check(LIBXML_DOTTED_VERSION === '2.9.9', 'Unexpected compile-time libxml');
check(LIBXML_LOADED_VERSION === '20909', 'Unexpected runtime libxml');
check(json_decode(json_encode(array('x' => 42)), true)['x'] === 42, 'JSON roundtrip');
check(preg_match('/^a[0-9]+$/u', 'a123') === 1, 'PCRE smoke');
check(mb_strlen('Grüße', 'UTF-8') === 5, 'mbstring smoke');
check(bcadd('1.1', '2.2', 1) === '3.3', 'bcmath smoke');
$dom = new DOMDocument();
check($dom->loadXML('<root><value>42</value></root>'), 'XML parsing');
check($dom->getElementsByTagName('value')->item(0)->textContent === '42', 'DOM content');
check(strlen(sodium_crypto_generichash('smoke')) === 32, 'Sodium smoke');
check(igbinary_unserialize(igbinary_serialize(array(42))) === array(42), 'igbinary roundtrip');
check(msgpack_unpack(msgpack_pack(array(42))) === array(42), 'msgpack roundtrip');
check(password_verify('synthetic-test', password_hash('synthetic-test', PASSWORD_ARGON2ID)), 'Argon2 roundtrip');
$data = array('ok' => true, 'php' => PHP_VERSION, 'sapi' => PHP_SAPI,
    'icu' => INTL_ICU_VERSION, 'libxml' => LIBXML_LOADED_VERSION,
    'pcre' => PCRE_VERSION, 'openssl' => OPENSSL_VERSION_TEXT,
    'required_extension_count' => count($required), 'upload_progress' => '0');
if (PHP_SAPI !== 'cli') {
    header('Content-Type: application/json');
}
echo json_encode($data, JSON_UNESCAPED_SLASHES), "\n";
