<?php

declare(strict_types=1);

namespace App\Ui\Messenger\Message;

final readonly class AuditLogMessage
{
    public function __construct(
        public int $orderId,
        public string $action,
    ) {
    }
}
