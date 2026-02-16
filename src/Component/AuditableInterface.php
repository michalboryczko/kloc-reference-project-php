<?php

declare(strict_types=1);

namespace App\Component;

/**
 * Interface for auditable components.
 *
 * Contract test patterns:
 * - Interface with all-scalar return type
 * - Used for multiple interface implementation testing
 */
interface AuditableInterface
{
    /**
     * @return array<string>
     */
    public function getAuditLog(): array;
}
