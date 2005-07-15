powerpc default:	powerpc.stub nosmp.stub cpufreq.stub common.stub
	@cat $^
%-smp:	%.stub smp.stub nocpufreq.stub common.stub
	@cat $^
%:	%.stub nosmp.stub nocpufreq.stub common.stub
	@cat $^
