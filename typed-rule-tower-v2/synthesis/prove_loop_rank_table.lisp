;;; Exact arithmetic theorem for a retained finite progress table, not code refinement.
(load (merge-pathnames "fim_native_formal_setup.lisp" *load-truename*))
(in-package #:lsip)
(dolist (file '("proof_term_v1" "proposition_v1" "checked_theorem_v1"
                "proof_environment_v1" "proof_program_v1" "proof_machine_checker_v1" "proof_machine_structured_checker_v1"))
  (load (merge-pathnames (format nil "lisp/~A.lisp" file) cl-user::*native-root*)))
(load (second sb-ext:*posix-argv*))
(fim-validate-native-subject-v1 *rank-transaction* :machine)
(defun retained-rank-v1 (state)
  (let ((phase (getf state :phase)) (remaining (getf state :remaining)))
    (unless (and (member phase '("ready" "waiting" "terminated") :test #'equal)
                 (integerp remaining) (<= 0 remaining 2))
      (error "Rank table state outside its declared finite domain"))
    (if (equal phase "terminated") 0
        (+ (* 2 remaining) (if (equal phase "ready") 1 2)))))
(defun rank-program-v1 (edges environment)
  (let ((instructions nil) (goal nil) (previous nil))
    (loop for edge in edges for n from 0 do
      (let* ((before (retained-rank-v1 (getf edge :before)))
             (after (retained-rank-v1 (getf edge :after)))
             (atom (make-proposition-atom-v1 :rank-less
                    (list (make-proof-constant-v1 :integer after)
                          (make-proof-constant-v1 :integer before))))
             (ref (list :edge n)))
        (push (make-proof-instruction-v1 :opcode :closed-eval :output ref :proposition atom) instructions)
        (if previous
            (let ((combined (list :conjunction n)))
              (push (make-proof-instruction-v1 :opcode :and-intro :output combined
                        :input-refs (list previous ref)) instructions)
              (setf previous combined goal (make-proposition-and-v1 goal atom)))
            (setf previous ref goal atom))))
    (unless previous (error "Cannot prove an empty rank table"))
    (push (make-proof-instruction-v1 :opcode :return :input-refs (list previous)) instructions)
    (make-proof-program-v1 :goal goal
      :environment-ref (proof-environment-v1-semantic-identity environment)
      :instructions (nreverse instructions))))
(let* ((table *rank-edges*)
       (environment (make-proof-environment-v1
                     :assumptions nil :theorems nil :closed-atoms nil :sort-domains nil
                     :sort-table '(:integer) :functions nil
                     :predicates (list (make-proof-environment-predicate-v1
                                       :ref :rank-less :argument-sorts '(:integer :integer)
                                       :evaluator-op :integer-less))))
       (program (rank-program-v1 table environment))
       (theorem (proof-machine-check-program-v1 program environment))
       (again (proof-machine-check-program-v1 program environment))
       (capability (make-formal-capability-v1
                    :capability-ref :finite-progress-table-ranking-v1
                    :input-surface-ref :retained-finite-progress-table
                    :output-judgment-surface-ref :checked-table-rank-decrease
                    :claim-classes '(:finite-progress-table-ranking)
                    :backend-ref :native-proof-machine-v1 :trusted-boundary-refs nil
                    :resource-policy-ref :finite-table-v1 :result-class :checked-theorem
                    :admission-relevance :finite-model-table-only
                    :authority-ref :fim-experiment-extension-v2))
       (raw (make-formal-obligation :id (list :rank-table (getf *rank-transaction* :model-digest))
                                  :source-carrier-id (getf *rank-transaction* :subject)
                                  :operation-id :finite-progress-table-ranking
                                  :payload-row (list :coordinates *rank-transaction* :table table)))
       (obligation (project-formal-obligation-v1 raw capability :source-ref *rank-transaction*
                    :claim-class :finite-progress-table-ranking :authority-ref :fim-experiment-extension-v2))
       (claim-id (list :fim :finite-progress-table-ranking (formal-obligation-v1-semantic-identity obligation)))
       (state (formal-claim-state-v1 (list (make-formal-claim-record-v1
                                          :claim-id claim-id :status :undischarged
                                          :obligation-ref (formal-obligation-v1-semantic-identity obligation)))))
       (translation (make-formal-translation-witness-v1
                       :source-formal-identity (getf *rank-transaction* :model-digest)
                       :source-state-ref (formal-claim-state-identity-v1 state)
                       :claim-id claim-id :claim-class :finite-progress-table-ranking
                       :translation-law-ref :retained-rank-table-to-integer-less-conjunction-v1
                       :capability capability :target-formal-kind :native-closed-arithmetic-conjunction
                       :target-payload-digest (proof-program-v1-program-identity program)
                       :status :projected :authority-ref :fim-experiment-extension-v2))
       (receipt (make-formal-proof-receipt-v1
                  :claim-id claim-id :formal-claim-state state :projection translation
                  :capability capability :obligation obligation :proof-program program
                  :proof-environment environment :checked-theorem again
                  :freshness-status :fresh :judgment :pass :authority-ref :fim-experiment-extension-v2)))
  (unless (equal (checked-theorem-v1-theorem-identity theorem) (checked-theorem-v1-theorem-identity again))
    (error "Deterministic theorem recheck changed identity"))
  ;; The original semantic projection, not generic receipt integrity, establishes scope.
  (unless (proposition-v1= (proof-program-v1-goal program) (checked-theorem-v1-root-proposition theorem))
    (error "Rank theorem covers a different proposition"))
  (let ((bad (copy-tree table)))
    (setf (getf (first bad) :after) (copy-tree (getf (first bad) :before)))
    (unless (handler-case (progn (proof-machine-check-program-v1 (rank-program-v1 bad environment) environment) nil)
              (error (e) (and (search "CLOSED-EVAL" (string-upcase (princ-to-string e))) t)))
      (error "Nondecreasing counterexample was not rejected by arithmetic checker")))
  (with-open-file (out (third sb-ext:*posix-argv*) :direction :output :if-exists :supersede)
    (let ((*print-readably* t) (*print-circle* t))
      (write (list :schema :native-finite-rank-proof-v1 :coordinates *rank-transaction*
                   :scope :retained-table-arithmetic-only :edges (length table)
                   :axioms nil :closed-atoms nil :runtime-correspondence :open
                   :program (proof-program-v1-form program)
                   :environment (proof-environment-v1-form environment)
                   :theorem (checked-theorem-v1-form theorem)
                   :receipt (formal-methods-carrier-form-v1 receipt)
                   :admission (formal-proof-receipt-v1-admission-row receipt)) :stream out)))
  (format t "NATIVE_RANK_PROOF_GREEN edges=~D theorem=~A executable=BLOCKED~%"
          (length table) (checked-theorem-v1-theorem-identity theorem)))
