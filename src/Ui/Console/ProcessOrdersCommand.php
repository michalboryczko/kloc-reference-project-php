<?php

declare(strict_types=1);

namespace App\Ui\Console;

use App\Service\OrderService;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * Console command for processing orders.
 *
 * Contract test patterns:
 * - #[AsCommand] attribute (detected via console.command tag)
 * - Creates CLI flow: Command → OrderService → Repository
 * - Tests CLI flow type in flow discovery
 */
#[AsCommand(
    name: 'app:process-orders',
    description: 'Process pending orders',
)]
final class ProcessOrdersCommand extends Command
{
    public function __construct(
        private readonly OrderService $orderService,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $order = $this->orderService->getOrder(1);

        if ($order !== null) {
            $output->writeln(sprintf('Processed order #%d', $order->id));
        }

        return Command::SUCCESS;
    }
}
