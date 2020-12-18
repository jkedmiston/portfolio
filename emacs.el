;; init.el --- Emacs configuration

;; INSTALL PACKAGES
;; --------------------------------------


(require 'package)

(add-to-list 'package-archives
       '("melpa-stable" . "http://stable.melpa.org/packages/"))

(setq inhibit-startup-message t) ;; hide the startup message
;;(custom-set-variables
;; (pyvenv-activate "/Users/johnedmiston/anaconda3/envs/myco")
;; https://github.com/jorgenschaefer/elpy
(package-initialize)
(elpy-enable)
(setq elpy-rpc-virtualenv-path 'current)
(require 'virtualenvwrapper)
(venv-initialize-interactive-shells) ;; if you want interactive shell support
(venv-initialize-eshell) ;; if you want eshell support
;; note that setting `venv-location` is not necessary if you
;; use the default location (`~/.virtualenvs`), or if the
;; the environment variable `WORKON_HOME` points to the right place
(setq venv-location "/Users/johnedmiston/anaconda3/envs/myco")

(pyvenv-activate "/Users/johnedmiston/anaconda3/envs/myco")
;; Enable Flycheck
(when (require 'flycheck nil t)
  (setq elpy-modules (delq 'elpy-module-flymake elpy-modules))
  (add-hook 'elpy-mode-hook 'flycheck-mode))

;; Enable autopep8
(require 'py-autopep8)
(add-hook 'elpy-mode-hook 'py-autopep8-enable-on-save)

(global-set-key (kbd "\C-c l") 'goto-line)
(global-set-key "\M-\r" 'shell-resync-dirs)
(setq-default indent-tabs-mode nil)
