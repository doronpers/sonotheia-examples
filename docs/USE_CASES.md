# Sonotheia Use Cases

> **Real-world integration scenarios** with complete code examples

This guide demonstrates how to combine Sonotheia API features to solve common business problems. Each use case includes context, workflow diagrams, and production-ready code.

---

## Table of Contents

- [Use Case 1: Financial Transaction Verification](#use-case-1-financial-transaction-verification)
- [Use Case 2: Call Center Fraud Detection](#use-case-2-call-center-fraud-detection)
- [Use Case 3: Voice MFA for High-Value Accounts](#use-case-3-voice-mfa-for-high-value-accounts)
- [Use Case 4: Compliance and SAR Workflows](#use-case-4-compliance-and-sar-workflows)
- [Use Case 5: Automated Voice Authentication](#use-case-5-automated-voice-authentication)
- [Use Case 6: Batch Processing for Security Review](#use-case-6-batch-processing-for-security-review)

---

## Use Case 1: Financial Transaction Verification

**Scenario:** A banking customer calls to initiate a wire transfer. You need to verify it's really them speaking, not a deepfake or voice clone.

**Business Need:** Prevent unauthorized transfers while maintaining good customer experience.

**Solution:** Combine deepfake detection with voice MFA for layered security.

### Workflow

```
Customer calls → Record audio → 
→ Step 1: Deepfake detection
   ├─ Score < 0.3: Proceed to MFA
   ├─ Score 0.3-0.7: Flag for review + MFA
   └─ Score > 0.7: Block + Human review

→ Step 2: Voice MFA (if passed step 1)
   ├─ Verified: Approve transaction
   └─ Failed: Block + Human review

→ Step 3: Submit SAR (if suspicious)
```

### Complete Implementation

```python
from client_enhanced import SonotheiaClientEnhanced
import logging

logger = logging.getLogger(__name__)

class TransactionVerifier:
    def __init__(self):
        self.client = SonotheiaClientEnhanced(
            max_retries=3,
            rate_limit_rps=2.0,
            enable_circuit_breaker=True
        )
    
    def verify_transaction(
        self,
        audio_path: str,
        enrollment_id: str,
        transaction_id: str,
        amount: float
    ) -> dict:
        """
        Verify a financial transaction using voice authentication.
        
        Returns:
            {
                'approved': bool,
                'reason': str,
                'requires_review': bool,
                'session_id': str
            }
        """
        session_id = f"txn_{transaction_id}"
        
        # Step 1: Deepfake Detection
        try:
            deepfake_result = self.client.detect_deepfake(
                audio_path,
                metadata={
                    'session_id': session_id,
                    'transaction_id': transaction_id,
                    'amount': amount
                }
            )
        except Exception as e:
            logger.error(f"Deepfake detection failed: {e}")
            return {
                'approved': False,
                'reason': 'Technical error - please try again',
                'requires_review': True,
                'session_id': session_id
            }
        
        score = deepfake_result['score']
        
        # High risk - immediate block
        if score > 0.7:
            logger.warning(f"High deepfake score {score} for {session_id}")
            self._submit_sar(session_id, 'block', 
                           f'High deepfake score: {score}')
            return {
                'approved': False,
                'reason': 'Voice verification failed',
                'requires_review': True,
                'session_id': session_id
            }
        
        # Medium risk - flag but continue
        requires_review = score >= 0.3
        if requires_review:
            logger.info(f"Medium risk score {score} for {session_id}")
        
        # Step 2: Voice MFA
        try:
            mfa_result = self.client.verify_mfa(
                audio_path,
                enrollment_id,
                context={
                    'session_id': session_id,
                    'transaction_id': transaction_id,
                    'deepfake_score': score
                }
            )
        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            return {
                'approved': False,
                'reason': 'Voice verification failed',
                'requires_review': True,
                'session_id': session_id
            }
        
        # Check MFA result
        if not mfa_result['verified']:
            logger.warning(f"MFA failed for {session_id}")
            self._submit_sar(session_id, 'deny',
                           f'MFA failed, confidence: {mfa_result["confidence"]}')
            return {
                'approved': False,
                'reason': 'Voice verification failed',
                'requires_review': True,
                'session_id': session_id
            }
        
        # Low confidence MFA - require review even if passed
        if mfa_result['confidence'] < 0.8:
            requires_review = True
        
        # Step 3: Submit SAR if flagged
        if requires_review:
            self._submit_sar(
                session_id, 
                'review',
                f'Deepfake score: {score}, MFA confidence: {mfa_result["confidence"]}'
            )
        
        return {
            'approved': True,
            'reason': 'Voice verified successfully',
            'requires_review': requires_review,
            'session_id': session_id,
            'deepfake_score': score,
            'mfa_confidence': mfa_result['confidence']
        }
    
    def _submit_sar(self, session_id: str, decision: str, reason: str):
        """Submit SAR for suspicious activity."""
        try:
            result = self.client.submit_sar(
                session_id,
                decision,
                reason,
                metadata={'submission_time': 'auto'}
            )
            logger.info(f"SAR submitted: {result['case_id']}")
        except Exception as e:
            logger.error(f"SAR submission failed: {e}")

# Usage
if __name__ == '__main__':
    verifier = TransactionVerifier()
    
    result = verifier.verify_transaction(
        audio_path='customer_call.wav',
        enrollment_id='enroll_customer123',
        transaction_id='TXN20240105001',
        amount=50000.00
    )
    
    if result['approved']:
        if result['requires_review']:
            print("✓ Transaction approved, flagged for review")
            print(f"  Deepfake score: {result['deepfake_score']}")
            print(f"  MFA confidence: {result['mfa_confidence']}")
        else:
            print("✓ Transaction approved")
    else:
        print("✗ Transaction blocked")
        print(f"  Reason: {result['reason']}")
```

**Key Features:**
- Layered security (deepfake + MFA)
- Risk-based decision making
- Automatic SAR submission
- Comprehensive error handling
- Production-ready retry logic

---

## Use Case 2: Call Center Fraud Detection

**Scenario:** Your call center receives thousands of calls daily. You need to detect potential fraud attempts in real-time without blocking legitimate customers.

**Business Need:** Balance security with customer experience at scale.

**Solution:** Batch process recorded calls with risk scoring and automated escalation.

### Workflow

```
Calls recorded → Batch process overnight →
→ Deepfake detection for all calls
→ Risk scoring (score + metadata)
→ High-risk calls → Alert security team
→ Medium-risk calls → Flag for callback
→ Low-risk calls → Archive
```

### Implementation (Node.js)

```javascript
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const pino = require('pino');

const logger = pino({ level: process.env.LOG_LEVEL || 'info' });

class CallCenterAnalyzer {
  constructor() {
    this.apiKey = process.env.SONOTHEIA_API_KEY;
    this.apiUrl = process.env.SONOTHEIA_API_URL || 'https://api.sonotheia.com';
    this.concurrency = parseInt(process.env.CONCURRENT_REQUESTS || '5');
  }

  async analyzeCallBatch(callDirectory) {
    const callFiles = this.getCallFiles(callDirectory);
    logger.info(`Processing ${callFiles.length} calls`);

    // Process in batches with concurrency limit
    const results = [];
    for (let i = 0; i < callFiles.length; i += this.concurrency) {
      const batch = callFiles.slice(i, i + this.concurrency);
      const batchResults = await Promise.all(
        batch.map(file => this.analyzeCall(file))
      );
      results.push(...batchResults);
    }

    // Generate risk report
    return this.generateRiskReport(results);
  }

  async analyzeCall(filePath) {
    const callId = path.basename(filePath, path.extname(filePath));
    
    try {
      const formData = new FormData();
      formData.append('audio', fs.createReadStream(filePath));
      formData.append('metadata', JSON.stringify({
        session_id: callId,
        source: 'call_center',
        timestamp: new Date().toISOString()
      }));

      const response = await axios.post(
        `${this.apiUrl}/v1/voice/deepfake`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            ...formData.getHeaders()
          },
          timeout: 30000
        }
      );

      const result = {
        call_id: callId,
        file_path: filePath,
        score: response.data.score,
        label: response.data.label,
        risk_level: this.calculateRiskLevel(response.data.score),
        session_id: response.data.session_id,
        timestamp: new Date().toISOString()
      };

      logger.info({ result }, `Processed call ${callId}`);
      return result;

    } catch (error) {
      logger.error({ error, call_id: callId }, 'Failed to process call');
      return {
        call_id: callId,
        file_path: filePath,
        error: error.message,
        risk_level: 'ERROR',
        timestamp: new Date().toISOString()
      };
    }
  }

  calculateRiskLevel(score) {
    if (score >= 0.7) return 'HIGH';
    if (score >= 0.4) return 'MEDIUM';
    return 'LOW';
  }

  generateRiskReport(results) {
    const report = {
      total_calls: results.length,
      high_risk: results.filter(r => r.risk_level === 'HIGH').length,
      medium_risk: results.filter(r => r.risk_level === 'MEDIUM').length,
      low_risk: results.filter(r => r.risk_level === 'LOW').length,
      errors: results.filter(r => r.error).length,
      high_risk_calls: results.filter(r => r.risk_level === 'HIGH'),
      medium_risk_calls: results.filter(r => r.risk_level === 'MEDIUM'),
      average_score: this.calculateAverage(results.map(r => r.score).filter(Boolean)),
      timestamp: new Date().toISOString()
    };

    // Save report
    fs.writeFileSync(
      'call_center_risk_report.json',
      JSON.stringify(report, null, 2)
    );

    // Alert on high-risk calls
    if (report.high_risk > 0) {
      this.alertSecurityTeam(report.high_risk_calls);
    }

    return report;
  }

  calculateAverage(numbers) {
    if (numbers.length === 0) return 0;
    return numbers.reduce((a, b) => a + b, 0) / numbers.length;
  }

  alertSecurityTeam(highRiskCalls) {
    // In production, integrate with your alerting system
    logger.warn({
      alert: 'HIGH_RISK_CALLS_DETECTED',
      count: highRiskCalls.length,
      calls: highRiskCalls
    }, 'High-risk calls detected - alerting security team');

    // Example: Send to alerting service
    // await axios.post('https://alerts.company.com/api/alert', {
    //   severity: 'high',
    //   title: 'Deepfake Detection Alert',
    //   message: `${highRiskCalls.length} high-risk calls detected`,
    //   calls: highRiskCalls
    // });
  }

  getCallFiles(directory) {
    return fs.readdirSync(directory)
      .filter(file => file.endsWith('.wav'))
      .map(file => path.join(directory, file));
  }
}

// Usage
(async () => {
  const analyzer = new CallCenterAnalyzer();
  const report = await analyzer.analyzeCallBatch('./recorded_calls');

  console.log('=== CALL CENTER RISK REPORT ===');
  console.log(`Total calls analyzed: ${report.total_calls}`);
  console.log(`High risk: ${report.high_risk}`);
  console.log(`Medium risk: ${report.medium_risk}`);
  console.log(`Low risk: ${report.low_risk}`);
  console.log(`Average score: ${report.average_score.toFixed(3)}`);
  
  if (report.high_risk > 0) {
    console.log('\n⚠️  HIGH RISK CALLS DETECTED');
    report.high_risk_calls.forEach(call => {
      console.log(`  - ${call.call_id}: score ${call.score}`);
    });
  }
})();
```

**Key Features:**
- Batch processing with concurrency control
- Risk scoring and categorization
- Automated alerting for high-risk calls
- Comprehensive reporting
- Error handling and resilience

---

## Use Case 3: Voice MFA for High-Value Accounts

**Scenario:** Customers with high-value accounts need additional security without friction.

**Business Need:** Strong authentication that's convenient and secure.

**Solution:** Voice-based MFA as a step-up authentication method.

### Workflow

```
Login attempt →
→ Username/password verified
→ Trigger voice MFA for high-value accounts
→ Customer speaks passphrase
→ Verify against enrolled voiceprint
→ Check deepfake score
→ Grant/deny access
```

### Implementation

```python
from client import SonotheiaClient
from datetime import datetime, timedelta
import hashlib

class VoiceMFAAuth:
    def __init__(self):
        self.client = SonotheiaClient()
        # In production, use a proper database
        self.mfa_attempts = {}
    
    def requires_voice_mfa(self, user_id: str, account_value: float) -> bool:
        """Determine if voice MFA is required."""
        # High-value accounts always require voice MFA
        if account_value > 100000:
            return True
        
        # Check for recent failed login attempts
        attempts = self.mfa_attempts.get(user_id, [])
        recent_failures = [
            a for a in attempts 
            if a['timestamp'] > datetime.now() - timedelta(hours=24)
            and not a['success']
        ]
        
        # Require MFA after 2 failed attempts
        return len(recent_failures) >= 2
    
    def authenticate_with_voice(
        self,
        user_id: str,
        audio_path: str,
        enrollment_id: str,
        session_context: dict = None
    ) -> dict:
        """
        Authenticate user with voice MFA.
        
        Returns:
            {
                'authenticated': bool,
                'reason': str,
                'requires_additional_verification': bool,
                'mfa_confidence': float,
                'deepfake_score': float
            }
        """
        session_id = f"mfa_{user_id}_{datetime.now().timestamp()}"
        
        # Step 1: Check for deepfake
        deepfake_result = self.client.detect_deepfake(
            audio_path,
            metadata={
                'session_id': session_id,
                'user_id': user_id,
                'auth_type': 'voice_mfa',
                **(session_context or {})
            }
        )
        
        deepfake_score = deepfake_result['score']
        
        # Immediate rejection for high deepfake scores
        if deepfake_score > 0.7:
            self._record_attempt(user_id, False, 'deepfake_detected')
            return {
                'authenticated': False,
                'reason': 'Voice verification failed',
                'requires_additional_verification': True,
                'deepfake_score': deepfake_score
            }
        
        # Step 2: Verify voice MFA
        mfa_result = self.client.verify_mfa(
            audio_path,
            enrollment_id,
            context={
                'session_id': session_id,
                'user_id': user_id,
                'deepfake_score': deepfake_score
            }
        )
        
        verified = mfa_result['verified']
        confidence = mfa_result['confidence']
        
        # Decision logic
        if verified and confidence >= 0.85 and deepfake_score < 0.3:
            # High confidence - approve
            self._record_attempt(user_id, True, 'success')
            return {
                'authenticated': True,
                'reason': 'Voice verified successfully',
                'requires_additional_verification': False,
                'mfa_confidence': confidence,
                'deepfake_score': deepfake_score
            }
        
        elif verified and confidence >= 0.7:
            # Medium confidence - approve but flag
            self._record_attempt(user_id, True, 'success_flagged')
            return {
                'authenticated': True,
                'reason': 'Voice verified with additional review',
                'requires_additional_verification': True,
                'mfa_confidence': confidence,
                'deepfake_score': deepfake_score
            }
        
        else:
            # Low confidence or not verified - reject
            self._record_attempt(user_id, False, 'mfa_failed')
            return {
                'authenticated': False,
                'reason': 'Voice verification failed',
                'requires_additional_verification': True,
                'mfa_confidence': confidence,
                'deepfake_score': deepfake_score
            }
    
    def _record_attempt(self, user_id: str, success: bool, reason: str):
        """Record authentication attempt for analysis."""
        if user_id not in self.mfa_attempts:
            self.mfa_attempts[user_id] = []
        
        self.mfa_attempts[user_id].append({
            'timestamp': datetime.now(),
            'success': success,
            'reason': reason
        })

# Usage
if __name__ == '__main__':
    auth = VoiceMFAAuth()
    
    # Check if MFA is required
    user_id = 'user123'
    account_value = 500000.00
    
    if auth.requires_voice_mfa(user_id, account_value):
        print("Voice MFA required for this account")
        
        # Perform voice authentication
        result = auth.authenticate_with_voice(
            user_id=user_id,
            audio_path='user_voice_sample.wav',
            enrollment_id='enroll_user123',
            session_context={
                'ip_address': '192.168.1.1',
                'device': 'mobile_app'
            }
        )
        
        if result['authenticated']:
            print("✓ Authentication successful")
            if result['requires_additional_verification']:
                print("  ⚠️  Flagged for additional review")
        else:
            print("✗ Authentication failed")
            print(f"  Reason: {result['reason']}")
```

**Key Features:**
- Risk-based MFA triggering
- Layered security (deepfake + voice match)
- Confidence-based decision making
- Attempt tracking and analysis
- Step-up authentication support

---

## Use Case 4: Compliance and SAR Workflows

**Scenario:** Financial institution must submit Suspicious Activity Reports (SARs) for potential fraud.

**Business Need:** Automated detection and reporting while maintaining compliance.

**Solution:** Integrated workflow from detection to SAR submission.

### Complete SAR Workflow

```python
from client import SonotheiaClient
from datetime import datetime
import json

class ComplianceWorkflow:
    def __init__(self):
        self.client = SonotheiaClient()
        self.sar_threshold = 0.6  # Configurable threshold
    
    def process_transaction_with_compliance(
        self,
        audio_path: str,
        transaction_details: dict
    ) -> dict:
        """
        Complete workflow: Detection → Decision → SAR submission.
        
        Args:
            audio_path: Path to recorded audio
            transaction_details: {
                'transaction_id': str,
                'customer_id': str,
                'amount': float,
                'type': str,
                'destination': str
            }
        
        Returns:
            {
                'approved': bool,
                'sar_submitted': bool,
                'sar_case_id': str or None,
                'decision_reason': str
            }
        """
        session_id = f"compliance_{transaction_details['transaction_id']}"
        
        # Step 1: Deepfake Detection
        detection_result = self.client.detect_deepfake(
            audio_path,
            metadata={
                'session_id': session_id,
                **transaction_details
            }
        )
        
        score = detection_result['score']
        
        # Step 2: Make Decision
        decision, reason = self._make_compliance_decision(
            score,
            transaction_details
        )
        
        # Step 3: Submit SAR if needed
        sar_case_id = None
        if decision in ['review', 'deny', 'block']:
            sar_case_id = self._submit_compliance_sar(
                session_id,
                decision,
                reason,
                score,
                transaction_details
            )
        
        return {
            'approved': decision == 'allow',
            'decision': decision,
            'sar_submitted': sar_case_id is not None,
            'sar_case_id': sar_case_id,
            'decision_reason': reason,
            'deepfake_score': score,
            'session_id': session_id
        }
    
    def _make_compliance_decision(
        self,
        deepfake_score: float,
        transaction_details: dict
    ) -> tuple:
        """Make risk-based decision with reason."""
        amount = transaction_details['amount']
        
        # Critical risk - immediate block
        if deepfake_score > 0.8:
            return 'block', f'Critical deepfake risk (score: {deepfake_score:.2f})'
        
        # High risk + high value - deny and review
        if deepfake_score > self.sar_threshold and amount > 10000:
            return 'deny', f'High risk transaction (score: {deepfake_score:.2f}, amount: ${amount:,.2f})'
        
        # Medium risk - flag for review
        if deepfake_score > self.sar_threshold:
            return 'review', f'Medium risk (score: {deepfake_score:.2f})'
        
        # Low risk - allow
        return 'allow', f'Low risk (score: {deepfake_score:.2f})'
    
    def _submit_compliance_sar(
        self,
        session_id: str,
        decision: str,
        reason: str,
        deepfake_score: float,
        transaction_details: dict
    ) -> str:
        """Submit SAR with full compliance metadata."""
        sar_metadata = {
            'submission_timestamp': datetime.now().isoformat(),
            'transaction_id': transaction_details['transaction_id'],
            'customer_id': transaction_details['customer_id'],
            'amount': transaction_details['amount'],
            'transaction_type': transaction_details['type'],
            'destination': transaction_details.get('destination'),
            'deepfake_score': deepfake_score,
            'automated_submission': True,
            'compliance_officer': 'system'
        }
        
        # Submit SAR
        result = self.client.submit_sar(
            session_id,
            decision,
            reason,
            metadata=sar_metadata
        )
        
        # Log for audit trail
        self._log_sar_submission(result, sar_metadata)
        
        return result['case_id']
    
    def _log_sar_submission(self, result: dict, metadata: dict):
        """Maintain audit log of SAR submissions."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'case_id': result['case_id'],
            'session_id': result['session_id'],
            'status': result['status'],
            'metadata': metadata
        }
        
        # In production, write to secure audit log system
        with open('sar_audit_log.json', 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

# Usage
if __name__ == '__main__':
    workflow = ComplianceWorkflow()
    
    result = workflow.process_transaction_with_compliance(
        audio_path='transaction_verification.wav',
        transaction_details={
            'transaction_id': 'TXN20240105001',
            'customer_id': 'CUST12345',
            'amount': 75000.00,
            'type': 'wire_transfer',
            'destination': 'International'
        }
    )
    
    print(f"Transaction decision: {result['decision']}")
    print(f"Reason: {result['decision_reason']}")
    
    if result['sar_submitted']:
        print(f"SAR submitted: {result['sar_case_id']}")
    
    if result['approved']:
        print("✓ Transaction approved")
    else:
        print("✗ Transaction blocked/flagged")
```

**Key Features:**
- Risk-based decision making
- Automatic SAR submission
- Complete audit trail
- Configurable thresholds
- Compliance metadata tracking

---

## Use Case 5: Automated Voice Authentication

**Scenario:** IVR system needs to authenticate callers before providing account access.

**Business Need:** Seamless voice authentication without agents.

### Quick Implementation

See [voice_routing_example.py](../examples/python/voice_routing_example.py) for a complete implementation with:
- Composite risk scoring
- Multi-factor routing decisions
- Transaction context integration
- Complete audit trail

**Key Features:**
- Real-time voice verification
- Risk-based routing
- Automated escalation
- Comprehensive logging

---

## Use Case 6: Batch Processing for Security Review

**Scenario:** Process 10,000+ recorded calls daily for security analysis.

**Business Need:** Efficient bulk processing with actionable insights.

### Implementation

See [batch-processor-enhanced.js](../examples/node/batch-processor-enhanced.js) for:
- Concurrent processing with rate limiting
- Progress tracking
- Summary statistics
- Error handling and retry logic

**Key Features:**
- High throughput processing
- Memory efficient
- Detailed reporting
- Production-ready patterns

---

## Integration Patterns

### Pattern 1: Sync vs Async Processing

**When to use synchronous:**
- Real-time authentication (MFA, login)
- Interactive voice response (IVR)
- Live fraud prevention

**When to use asynchronous (webhooks):**
- Batch processing
- Non-blocking workflows
- Background analysis

### Pattern 2: Error Handling Strategy

```python
from client_enhanced import SonotheiaClientEnhanced

# Production-ready error handling
client = SonotheiaClientEnhanced(
    max_retries=3,
    rate_limit_rps=2.0,
    enable_circuit_breaker=True
)

try:
    result = client.detect_deepfake(audio_path)
except CircuitBreakerOpen:
    # API is down, use fallback
    result = fallback_verification(audio_path)
except RateLimitExceeded:
    # Too many requests, queue for later
    queue_for_retry(audio_path)
except Exception as e:
    # Other errors, log and alert
    logger.error(f"Unexpected error: {e}")
    alert_on_call_team()
```

### Pattern 3: Multi-Stage Verification

```
Stage 1: Quick screening (deepfake detection)
  ↓ (if suspicious)
Stage 2: Voice MFA verification
  ↓ (if still uncertain)
Stage 3: Human review + additional context
```

---

## Best Practices Summary

1. **Layer your security**: Combine deepfake detection with MFA
2. **Use risk-based decisions**: Not all situations require the same rigor
3. **Implement proper retry logic**: Network issues happen
4. **Log everything**: Audit trails are critical for compliance
5. **Monitor and alert**: Track high-risk activities in real-time
6. **Test with real data**: Synthetic tests don't catch everything
7. **Have fallback procedures**: What happens when the API is down?

---

## Additional Resources

- **[Best Practices](BEST_PRACTICES.md)** - Production integration guidelines
- **[Enhanced Examples](ENHANCED_EXAMPLES.md)** - Advanced patterns
- **[Python Examples](../examples/python/)** - Complete implementations
- **[Node.js Examples](../examples/node/)** - Batch processing patterns
- **[FAQ](FAQ.md)** - Common questions

---

## Need Help?

**Questions about these use cases?**
- Open a [GitHub Discussion](https://github.com/doronpers/sonotheia-examples/discussions)
- Contact your Sonotheia integration engineer

**Want to contribute your use case?**
- See [Contributing Guide](../CONTRIBUTING.md)
- Share your implementation patterns!

---

**Ready to implement?** Start with [Getting Started](GETTING_STARTED.md) or dive into [code examples](../examples/).
