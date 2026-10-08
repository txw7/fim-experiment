;;; No implementation theorem exists yet: exercise the original owner's rejection.
(require :asdf)
(defparameter *native-root* #p"/home/user0/ORCHESTRATION/worktrees/goggles-vm-feedback-47fe6800/")
(asdf:initialize-source-registry `(:source-registry (:directory ,*native-root*) :inherit-configuration))
(setf *compile-verbose* nil *compile-print* nil)
(asdf:load-system "lsip")
(in-package #:lsip)
(load (second sb-ext:*posix-argv*))
(unless (and (getf *fim-transaction* :subject) (getf *fim-transaction* :snapshot)
             (getf *fim-transaction* :candidate-digest))
  (error "FIM gate requires exact candidate coordinates"))
(let ((rejected
        (handler-case
            (progn (formal-proof-receipt-v1-admission-row nil) nil)
          (error (e) (and (search "Formal admission requires FormalProofReceiptV1" (princ-to-string e)) t)))))
  (unless rejected (error "Missing implementation proof did not block native admission"))
  (format t "~S~%" (list :schema :fim-native-proof-gate-v1 :transaction *fim-transaction*
                         :owner :formal-proof-receipt-v1-admission-row :missing-proof-rejected t
                         :implementation-proof :open :executable-admission nil)))
