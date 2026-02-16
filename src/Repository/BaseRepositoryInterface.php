<?php

declare(strict_types=1);

namespace App\Repository;

/**
 * Base repository interface for all repositories.
 *
 * Contract test patterns:
 * - Interface extending interface chain
 * - Base interface with generic method
 */
interface BaseRepositoryInterface
{
    /**
     * @return array<mixed>
     */
    public function findAll(): array;
}
