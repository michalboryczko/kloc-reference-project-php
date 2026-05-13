<?php

declare(strict_types=1);

namespace App\Ui\Console;

use App\Service\ReportService;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * Console command for generating reports.
 *
 * Contract test patterns:
 * - #[AsCommand] attribute (detected via console.command tag)
 * - Creates CLI flow: Command → ReportService (→ dispatches event → event flow)
 * - Tests CLI flow type in flow discovery
 * - ReportService injects EventDispatcherInterface → trigger cross-reference
 */
#[AsCommand(
    name: 'app:process-reports',
    description: 'Generate and process reports',
)]
final class ProcessReportsCommand extends Command
{
    public function __construct(
        private readonly ReportService $reportService,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $reportId = $this->reportService->generateReport('daily');
        $output->writeln(sprintf('Generated report: %s', $reportId));

        return Command::SUCCESS;
    }
}
