"""
Safety Pipeline - Integration wrapper for all safety checks
"""
from typing import Dict, Any, Optional

from .guardrails import OutputGuardrails, SafetyLevel
from .validator import OutputValidator
from .fact_checker import FactChecker
from .confidence import ConfidenceScorer
from .self_correction import SelfCorrection


class SafetyPipeline:
    """
    Unified safety pipeline that runs all protection layers.
    Integrates with agent outputs.
    """
    
    def __init__(
        self,
        safety_level: SafetyLevel = SafetyLevel.STANDARD,
        cve_db=None,
        auto_correct: bool = True
    ):
        self.guardrails = OutputGuardrails(safety_level)
        self.validator = OutputValidator()
        self.fact_checker = FactChecker(cve_db=cve_db)
        self.confidence_scorer = ConfidenceScorer()
        self.self_correction = SelfCorrection()
        
        self.auto_correct = auto_correct
        self.safety_stats = {
            'outputs_checked': 0,
            'violations_found': 0,
            'auto_corrected': 0,
            'rejected': 0
        }
    
    def check_output(
        self,
        output: str,
        context: Optional[Dict] = None,
        schema_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run complete safety pipeline on output
        
        Returns:
            Dict with keys:
                - passed: bool
                - confidence: ConfidenceScore
                - corrected_output: str (if auto-corrected)
                - issues: list of found issues
                - should_retry: bool
                - should_alert: bool
        """
        self.safety_stats['outputs_checked'] += 1
        
        issues = []
        fact_corrections = []
        
        # Layer 1: Guardrails
        guardrail_result = self.guardrails.check(output, context)
        if not guardrail_result.passed:
            issues.extend(guardrail_result.violations)
        
        # Layer 2: Validation
        validation_result = None
        if schema_name:
            validation_result = self.validator.validate_json(output, schema_name)
        else:
            validation_result = self.validator.validate_command_output(output)
        
        if validation_result.errors:
            issues.extend(validation_result.errors)
        if validation_result.warnings:
            issues.extend(validation_result.warnings)
        
        # Layer 3: Fact Checking
        fact_results = self.fact_checker.check_output(output, context)
        for result in fact_results:
            if result.status.value in ['contradicted', 'unknown']:
                issues.append(f"Fact check: {result.claim} - {result.status.value}")
                if result.correction:
                    fact_corrections.append(result.correction)
        
        # Layer 4: Consistency Check
        consistency_score = 1.0
        if context and 'memory_context' in context:
            consistency = self.validator.validate_factual_consistency(
                output, context['memory_context']
            )
            consistency_score = 1.0 - consistency.confidence_impact
        
        # Calculate Confidence
        confidence = self.confidence_scorer.calculate(
            guardrail_result=guardrail_result,
            validation_result=validation_result,
            fact_check_results=fact_results,
            consistency_score=consistency_score
        )
        
        result = {
            'passed': confidence.score >= 0.6,
            'confidence': confidence,
            'corrected_output': output,
            'issues': issues,
            'should_retry': False,
            'should_alert': False
        }
        
        # Auto-correction
        if issues and self.auto_correct:
            correction = self.self_correction.attempt_correction(
                output, issues, fact_corrections
            )
            if correction['success']:
                result['corrected_output'] = correction['corrected']
                result['auto_corrected'] = True
                self.safety_stats['auto_corrected'] += 1
                
                # Re-check confidence
                if confidence.score < 0.6:
                    result['should_retry'] = True
        
        # Determine actions
        if confidence.score < 0.6:
            result['should_retry'] = True
            self.safety_stats['rejected'] += 1
        
        if confidence.level in ['low', 'critical']:
            result['should_alert'] = True
        
        if issues:
            self.safety_stats['violations_found'] += len(issues)
        
        return result
    
    def get_retry_prompt(self, original_prompt: str, check_result: Dict) -> str:
        """Generate improved prompt for retry"""
        return self.self_correction.generate_retry_prompt(
            original_prompt,
            check_result['issues'],
            check_result['confidence'].breakdown
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            **self.safety_stats,
            'guardrail_stats': self.guardrails.get_stats(),
            'fact_check_stats': self.fact_checker.get_stats(),
            'correction_stats': self.self_correction.get_correction_stats()
        }
