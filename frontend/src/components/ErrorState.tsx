export const ErrorState = ({ message }: { message: string }) => (
  <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
    <h3 className="font-bold">Error</h3>
    <p>{message}</p>
  </div>
);