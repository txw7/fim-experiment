(require :asdf)
(push :shg-library *features*)
(load (merge-pathnames "../shg-stack.lisp" (uiop:pathname-directory-pathname *load-truename*)))
(asdf:load-system "lsip")
;; Run unchanged native checker bodies with the full system loaded once.
;; The upstream shell suite force-recompiles the unrelated full lsip system per script.
(dolist (name '("check_semantic_bundle_registry_core_v1" "check_semantic_bundle_relation_incidence_v1"
               "check_semantic_bundle_generation_v1" "check_semantic_bundle_address_v1"
               "check_semantic_bundle_route_v1"))
 (let ((*package* (find-package :cl-user)) (active nil))
  (with-open-file (s (merge-pathnames (format nil "scripts/~A.lisp" name) cl-user::*mc-root*))
   (read-line s) ; shebang
   (loop for form = (read s nil :end) until (eq form :end) do
    (when (and (consp form) (eq (first form) 'in-package)) (setf active t))
    (when active (eval form))))))
(format t "NATIVE_PROFILE_CHECKS_GREEN scripts=5~%")
