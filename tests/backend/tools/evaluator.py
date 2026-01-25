#!/usr/bin/env python3
"""
DAS Evaluation Framework
Industry-Level Test Evaluation Script

This script:
1. Runs pytest with coverage and JUnit XML output
2. Parses test results
3. Calculates metrics: Code Coverage, Defect Density, Success Rate
4. Outputs status report: CRITICAL_FAILURE, STABLE, or PROD_READY

Reference: ISO/IEC/IEEE 29119, ISTQB Test Metrics
"""

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class TestResult:
    """Represents a single test result."""
    name: str
    classname: str
    time: float
    status: str  # passed, failed, skipped, error
    failure_message: Optional[str] = None


@dataclass
class EvaluationMetrics:
    """Container for all evaluation metrics."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    success_rate: float
    code_coverage: float
    defect_density: float
    execution_time: float
    status: str  # CRITICAL_FAILURE, STABLE, PROD_READY


class TestEvaluator:
    """
    Main evaluator class that runs tests and generates reports.
    """
    
    # Status thresholds (configurable for different projects)
    THRESHOLDS = {
        "prod_ready": {
            "success_rate": 95.0,
            "code_coverage": 80.0,
            "max_defect_density": 0.05,
        },
        "stable": {
            "success_rate": 85.0,
            "code_coverage": 60.0,
            "max_defect_density": 0.15,
        },
        # Below stable = CRITICAL_FAILURE
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tests_dir = project_root / "tests"
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        self.junit_xml = self.reports_dir / "junit_report.xml"
        self.coverage_xml = self.reports_dir / "coverage.xml"
        self.coverage_json = self.reports_dir / "coverage.json"
    
    def run_tests(self, markers: Optional[List[str]] = None, verbose: bool = True) -> int:
        """
        Execute pytest with coverage.
        
        Args:
            markers: Optional list of pytest markers to filter tests
            verbose: Enable verbose output
            
        Returns:
            pytest exit code
        """
        print("=" * 60)
        print("DAS EVALUATION FRAMEWORK")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Project Root: {self.project_root}")
        print("-" * 60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            f"--junitxml={self.junit_xml}",
            f"--cov={self.project_root / 'src'}",
            f"--cov-report=xml:{self.coverage_xml}",
            f"--cov-report=json:{self.coverage_json}",
            "--cov-report=term",
            "-v" if verbose else "-q",
        ]
        
        if markers:
            cmd.extend(["-m", " or ".join(markers)])
        
        print(f"\nRunning: {' '.join(cmd)}\n")
        print("-" * 60)
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        return result.returncode
    
    def parse_junit_xml(self) -> List[TestResult]:
        """Parse JUnit XML report and extract test results."""
        if not self.junit_xml.exists():
            print(f"ERROR: JUnit XML not found at {self.junit_xml}")
            return []
        
        tree = ET.parse(self.junit_xml)
        root = tree.getroot()
        
        results = []
        
        for testcase in root.iter("testcase"):
            name = testcase.get("name", "unknown")
            classname = testcase.get("classname", "unknown")
            time_str = testcase.get("time", "0")
            
            try:
                time_val = float(time_str)
            except ValueError:
                time_val = 0.0
            
            # Determine status
            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped = testcase.find("skipped")
            
            if failure is not None:
                status = "failed"
                message = failure.get("message", failure.text)
            elif error is not None:
                status = "error"
                message = error.get("message", error.text)
            elif skipped is not None:
                status = "skipped"
                message = skipped.get("message", "")
            else:
                status = "passed"
                message = None
            
            results.append(TestResult(
                name=name,
                classname=classname,
                time=time_val,
                status=status,
                failure_message=message
            ))
        
        return results
    
    def parse_coverage(self) -> float:
        """Parse coverage JSON and extract percentage."""
        if not self.coverage_json.exists():
            print(f"WARNING: Coverage JSON not found at {self.coverage_json}")
            return 0.0
        
        try:
            with open(self.coverage_json, "r") as f:
                data = json.load(f)
            
            return data.get("totals", {}).get("percent_covered", 0.0)
        except Exception as e:
            print(f"ERROR parsing coverage: {e}")
            return 0.0
    
    def calculate_metrics(self, results: List[TestResult], coverage: float) -> EvaluationMetrics:
        """Calculate all evaluation metrics."""
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        
        execution_time = sum(r.time for r in results)
        
        # Success rate (excluding skipped)
        executed = total - skipped
        success_rate = (passed / executed * 100) if executed > 0 else 0.0
        
        # Defect density = failed tests / total tests
        defect_density = (failed + errors) / total if total > 0 else 0.0
        
        # Determine status
        status = self._determine_status(success_rate, coverage, defect_density)
        
        return EvaluationMetrics(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            success_rate=round(success_rate, 2),
            code_coverage=round(coverage, 2),
            defect_density=round(defect_density, 4),
            execution_time=round(execution_time, 3),
            status=status
        )
    
    def _determine_status(self, success_rate: float, coverage: float, defect_density: float) -> str:
        """Determine overall project status based on thresholds."""
        prod = self.THRESHOLDS["prod_ready"]
        stable = self.THRESHOLDS["stable"]
        
        if (success_rate >= prod["success_rate"] and 
            coverage >= prod["code_coverage"] and 
            defect_density <= prod["max_defect_density"]):
            return "PROD_READY"
        
        if (success_rate >= stable["success_rate"] and 
            coverage >= stable["code_coverage"] and 
            defect_density <= stable["max_defect_density"]):
            return "STABLE"
        
        return "CRITICAL_FAILURE"
    
    def generate_report(self, metrics: EvaluationMetrics, failed_tests: List[TestResult]) -> str:
        """Generate a formatted status report."""
        status_emoji = {
            "PROD_READY": "[PASS]",
            "STABLE": "[WARN]",
            "CRITICAL_FAILURE": "[FAIL]"
        }
        
        report = []
        report.append("\n" + "=" * 60)
        report.append("EVALUATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Status banner
        emoji = status_emoji.get(metrics.status, "❓")
        report.append(f"STATUS: {emoji} {metrics.status} {emoji}")
        report.append("")
        
        # Metrics table
        report.append("-" * 40)
        report.append("METRICS SUMMARY")
        report.append("-" * 40)
        report.append(f"  Total Tests:       {metrics.total_tests}")
        report.append(f"  Passed:            {metrics.passed}")
        report.append(f"  Failed:            {metrics.failed}")
        report.append(f"  Errors:            {metrics.errors}")
        report.append(f"  Skipped:           {metrics.skipped}")
        report.append(f"  Success Rate:      {metrics.success_rate}%")
        report.append(f"  Code Coverage:     {metrics.code_coverage}%")
        report.append(f"  Defect Density:    {metrics.defect_density}")
        report.append(f"  Execution Time:    {metrics.execution_time}s")
        report.append("")
        
        # Thresholds reference
        report.append("-" * 40)
        report.append("THRESHOLD REFERENCE")
        report.append("-" * 40)
        report.append("  PROD_READY:")
        report.append(f"    - Success Rate >= {self.THRESHOLDS['prod_ready']['success_rate']}%")
        report.append(f"    - Code Coverage >= {self.THRESHOLDS['prod_ready']['code_coverage']}%")
        report.append(f"    - Defect Density <= {self.THRESHOLDS['prod_ready']['max_defect_density']}")
        report.append("  STABLE:")
        report.append(f"    - Success Rate >= {self.THRESHOLDS['stable']['success_rate']}%")
        report.append(f"    - Code Coverage >= {self.THRESHOLDS['stable']['code_coverage']}%")
        report.append(f"    - Defect Density <= {self.THRESHOLDS['stable']['max_defect_density']}")
        report.append("")
        
        # Failed tests details
        if failed_tests:
            report.append("-" * 40)
            report.append("FAILED TESTS DETAIL")
            report.append("-" * 40)
            for test in failed_tests:
                report.append(f"  [X] {test.classname}::{test.name}")
                if test.failure_message:
                    # Truncate long messages
                    msg = test.failure_message[:200] + "..." if len(test.failure_message) > 200 else test.failure_message
                    report.append(f"      └─ {msg}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_json_report(self, metrics: EvaluationMetrics, filepath: Optional[Path] = None) -> None:
        """Save metrics as JSON for CI/CD integration."""
        if filepath is None:
            filepath = self.reports_dir / "evaluation_report.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "status": metrics.status,
            "metrics": {
                "total_tests": metrics.total_tests,
                "passed": metrics.passed,
                "failed": metrics.failed,
                "errors": metrics.errors,
                "skipped": metrics.skipped,
                "success_rate": metrics.success_rate,
                "code_coverage": metrics.code_coverage,
                "defect_density": metrics.defect_density,
                "execution_time": metrics.execution_time,
            },
            "thresholds": self.THRESHOLDS,
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"JSON report saved to: {filepath}")
    
    def evaluate(self, run_tests: bool = True, markers: Optional[List[str]] = None) -> EvaluationMetrics:
        """
        Main evaluation pipeline.
        
        Args:
            run_tests: If True, run pytest. If False, parse existing reports.
            markers: Optional pytest markers to filter tests
            
        Returns:
            EvaluationMetrics object
        """
        if run_tests:
            exit_code = self.run_tests(markers)
            print(f"\nPytest exit code: {exit_code}")
        
        # Parse results
        results = self.parse_junit_xml()
        coverage = self.parse_coverage()
        
        # Calculate metrics
        metrics = self.calculate_metrics(results, coverage)
        
        # Get failed tests for detail report
        failed_tests = [r for r in results if r.status in ("failed", "error")]
        
        # Generate and print report
        report = self.generate_report(metrics, failed_tests)
        print(report)
        
        # Save JSON report
        self.save_json_report(metrics)
        
        return metrics


def main():
    """Command-line interface for the evaluator."""
    parser = argparse.ArgumentParser(
        description="DAS Test Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluator.py                    # Run all tests and evaluate
  python evaluator.py --no-run           # Evaluate existing reports only
  python evaluator.py -m functional      # Run only functional tests
  python evaluator.py -m "safety stress" # Run safety and stress tests
        """
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Path to project root directory"
    )
    
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Skip running tests, only parse existing reports"
    )
    
    parser.add_argument(
        "-m", "--markers",
        nargs="+",
        help="Pytest markers to filter tests (e.g., functional integration)"
    )
    
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Custom path for JSON report output"
    )
    
    args = parser.parse_args()
    
    evaluator = TestEvaluator(args.project_root)
    
    try:
        metrics = evaluator.evaluate(
            run_tests=not args.no_run,
            markers=args.markers
        )
        
        if args.json_output:
            evaluator.save_json_report(metrics, args.json_output)
        
        # Exit with appropriate code based on status
        if metrics.status == "CRITICAL_FAILURE":
            sys.exit(1)
        elif metrics.status == "STABLE":
            sys.exit(0)
        else:  # PROD_READY
            sys.exit(0)
            
    except Exception as e:
        print(f"EVALUATION ERROR: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
