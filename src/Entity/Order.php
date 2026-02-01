<?php

declare(strict_types=1);

namespace App\Entity;

use DateTimeImmutable;

final readonly class Order
{
    public function __construct(
        public int $id,
        public string $customerEmail,
        public string $productId,
        public int $quantity,
        public string $status,
        public DateTimeImmutable $createdAt,
    ) {
    }
}
