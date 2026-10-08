(load (merge-pathnames "fim_native_formal_setup.lisp" *load-truename*))
(in-package #:lsip)
(load (second sb-ext:*posix-argv*))
(fim-validate-native-subject-v1 *fim-transaction* :operation)
(let* ((coordinates (copy-tree *fim-transaction*))
       (source (symbolic-semantic-digest-v1 coordinates))
       (capability
         (make-formal-capability-v1
          :capability-ref :proposed-fim-kani-adapter-v1
          :input-surface-ref :exact-rust-candidate-and-harness
          :output-judgment-surface-ref :bounded-kani-result
          :claim-classes '(:fim-implementation-correspondence)
          :backend-ref :kani-0.67.0
          :trusted-boundary-refs '(:rustc-kani-compiler :cbmc :harness-generator)
          :resource-policy-ref :bounded-verification-profile-v1
          :result-class :bounded-symbolic-check
          :admission-relevance :evidence-only
          :authority-ref :fim-experiment-extension-v2))
       (raw
         (make-formal-obligation
          :id (list :fim-correspondence source)
          :source-carrier-id (getf coordinates :subject)
          :source-node-kind :operation
          :operation-id :accept-completion
          :obligation-kind :implementation-correspondence
          :backend :kani :payload-row coordinates))
       (obligation
         (project-formal-obligation-v1 raw capability
          :source-ref coordinates :claim-class :fim-implementation-correspondence
          :authority-ref :fim-experiment-extension-v2))
       (claim-id (list :fim :implementation-correspondence source))
       (claim
         (make-formal-claim-record-v1
          :claim-id claim-id :status :undischarged
          :obligation-ref (formal-obligation-v1-semantic-identity obligation)))
       (state (formal-claim-state-v1 (list claim)))
       (translation
         (make-formal-translation-witness-v1
          :source-formal-identity source
          :source-state-ref (formal-claim-state-identity-v1 state)
          :claim-id claim-id :claim-class :fim-implementation-correspondence
          :translation-law-ref :proposed-kani-to-native-proof-correspondence-v1
          :capability capability :target-formal-kind :kani-bounded-rust
          :target-payload-digest (getf coordinates :report-digest)
          :unsupported-constructs '(:native-kani-theorem-import-not-established)
          :status :unsupported :authority-ref :fim-experiment-extension-v2))
       (receipt
         (make-formal-proof-receipt-v1
          :claim-id claim-id :formal-claim-state state
          :projection translation :capability capability :obligation obligation
          :certificate-ref (list :external-kani-report (getf coordinates :report-digest))
          :freshness-status :fresh :judgment :unknown
          :authority-ref :fim-experiment-extension-v2))
       (form (formal-methods-carrier-form-v1 receipt)))
  (validate-formal-methods-carrier-form-v1 form)
  (unless (handler-case (progn (formal-proof-receipt-v1-admission-row receipt) nil)
            (error (e) (and (search "not a fresh passing admission witness" (princ-to-string e)) t)))
    (error "Open implementation receipt did not block native admission"))
  (with-open-file (out (third sb-ext:*posix-argv*) :direction :output :if-exists :supersede)
    (let ((*print-readably* t) (*print-circle* t))
      (write (list :schema :native-fim-open-obligation-v1 :coordinates coordinates
                   :capability (formal-methods-carrier-form-v1 capability)
                   :obligation (formal-methods-carrier-form-v1 obligation)
                   :claim-state state
                   :translation (formal-methods-carrier-form-v1 translation)
                   :receipt form :executable-admission nil) :stream out)))
  (format t "NATIVE_FIM_OBLIGATION_GREEN subject=~A receipt=~A implementation-proof=OPEN executable=BLOCKED~%"
          (getf coordinates :subject) (formal-proof-receipt-v1-semantic-identity receipt)))
