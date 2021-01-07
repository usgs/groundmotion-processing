# Removing Instrument Response

The `remove_response` subsection of `processing` in the config file
controls the options for removing instrument response. For strong
motion instruments, a simple sesnsitivity correction is applied to
convert from counts to physical units, and sometimes this is done
by the readers or is not doen at all since often times strong motion
data is often distributed after conversion from counts to physical
units.
