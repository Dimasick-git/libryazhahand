#---------------------------------------------------------------------------------
# RyazhaHand library configuration
# Auto-detects libryazhahand directory location.
#
# Подключается в Makefile оверлея одной строкой:
#   include ${TOPDIR}/lib/libryazhahand/ryazhahand.mk
#---------------------------------------------------------------------------------

TOPDIR ?= $(CURDIR)

# Absolute path of this .mk file directory.
RYZ_ABS := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

# Relative path from TOPDIR (fallback to absolute if .mk lies outside TOPDIR).
RYZ_DIR := $(subst $(TOPDIR)/,,$(RYZ_ABS))
ifeq ($(RYZ_DIR),$(RYZ_ABS))
  RYZ_DIR := $(RYZ_ABS)
endif

SOURCES += \
  $(RYZ_DIR)/common \
  $(RYZ_DIR)/libryazha/source \
  $(RYZ_DIR)/libtesla/source

INCLUDES += \
  $(RYZ_DIR)/common \
  $(RYZ_DIR)/libryazha/include \
  $(RYZ_DIR)/libtesla/include
